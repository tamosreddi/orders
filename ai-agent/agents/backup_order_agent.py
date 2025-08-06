"""
BACKUP VERSION - Streamlined Order Agent implementation for pilot testing.

Simplified 6-step workflow:
1. Get conversation context (recent messages + orders)
2. Analyze message with OpenAI (intent + products)  
3. Classify intent (BUY/QUESTION/COMPLAINT/etc)
4. Extract products (if BUY intent)
5. Validate against catalog (simplified)
6. Create order (if confident) + update message

Removed: Complex product matching, conversation AI, retry mechanisms.
Added: Simple OpenAI calls, linear workflow, easier debugging.
"""

from __future__ import annotations as _annotations

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from config.settings import settings
from services.database import DatabaseService
from services.product_matcher import ProductMatcher, ProductMatch, MatchResult
from schemas.message import MessageAnalysis, MessageIntent, ExtractedProduct
from schemas.order import OrderCreation, OrderProduct
from tools.supabase_tools import (
    get_recent_messages_for_context,
    get_recent_orders,
    update_message_ai_data,
    create_order,
    fetch_product_catalog
)

logger = logging.getLogger(__name__)


@dataclass
class StreamlinedAgentDeps:
    """Enhanced dependencies with intelligent product matching."""
    database: DatabaseService
    distributor_id: str
    product_matcher: ProductMatcher


# Enhanced system prompt for OpenAI with structured output
SYSTEM_PROMPT = """
You are an AI assistant for a B2B food distributor processing WhatsApp orders in Spanish and English.

Your job is to analyze customer messages and extract order information.

INTENT CLASSIFICATION:
- BUY: Customer wants to purchase products (e.g., "quiero", "necesito", "dame")
- QUESTION: Customer asking about products/services  
- COMPLAINT: Customer has an issue with order/service
- FOLLOW_UP: Customer referencing previous conversation
- OTHER: General conversation or greetings

PRODUCT EXTRACTION (for BUY intents):
Extract all products with quantities and units. Return in this JSON format:

```json
{
  "intent": "BUY",
  "confidence": 0.85,
  "reasoning": "Customer expressing purchase intent",
  "products": [
    {
      "name": "aceite de canola",
      "quantity": 1,
      "unit": "litro",
      "original_text": "un litro de aceite de canola"
    }
  ]
}
```

SPANISH NUMBER EXAMPLES:
- "un/una" = 1
- "dos" = 2  
- "tres" = 3
- "media docena" = 6
- "una docena" = 12

IMPORTANT: Always extract the exact product name as mentioned by the customer.
"""

# Initialize simple agent
streamlined_agent = Agent(
    model=OpenAIModel(settings.openai_model),
    system_prompt=SYSTEM_PROMPT,
    deps_type=StreamlinedAgentDeps,
    retries=2
)


class StreamlinedOrderProcessor:
    """
    Simplified order processor with linear 6-step workflow.
    
    Designed for pilot testing - easy to debug, reliable processing.
    """
    
    def __init__(self, database: DatabaseService, distributor_id: str):
        """Initialize the streamlined processor with intelligent product matching."""
        self.database = database
        self.distributor_id = distributor_id
        self.product_matcher = ProductMatcher()
        self.deps = StreamlinedAgentDeps(
            database=database,
            distributor_id=distributor_id,
            product_matcher=self.product_matcher
        )
        logger.info(f"Initialized StreamlinedOrderProcessor with intelligent product matching for distributor {distributor_id}")
    
    async def process_message(self, message_data: Dict[str, Any]) -> Optional[MessageAnalysis]:
        """
        Process message through streamlined 6-step workflow.
        
        Args:
            message_data: Message from webhook with id, content, customer_id, etc.
            
        Returns:
            MessageAnalysis if successful, None if failed
        """
        start_time = time.time()
        message_id = message_data.get('id', '')
        content = message_data.get('content', '').strip()
        customer_id = message_data.get('customer_id', '')
        conversation_id = message_data.get('conversation_id', '')
        
        logger.info(f"🔄 Processing message {message_id}: '{content[:50]}...'")
        
        try:
            # STEP 1: Get conversation context (simplified)
            context = await self._get_simple_context(conversation_id, customer_id)
            
            # STEP 2: Analyze message with OpenAI (intent + products)
            analysis_result = await self._analyze_with_openai(content, context)
            if not analysis_result:
                logger.error(f"❌ Failed to analyze message {message_id}")
                return None
            
            intent, products = analysis_result
            
            # STEP 3: Create MessageAnalysis object
            analysis = MessageAnalysis(
                message_id=message_id,
                intent=intent,
                extracted_products=products,
                customer_notes=None,
                delivery_date=None,
                processing_time_ms=0  # Will set at end
            )
            
            # STEP 4: Intelligent product validation with catalog matching
            if products and intent.intent == "BUY":
                validation_result = await self._intelligent_product_validation(
                    products, content, conversation_id
                )
                analysis.extracted_products = validation_result.get('validated_products', [])
                analysis.requires_clarification = validation_result.get('requires_clarification', False)
                analysis.suggested_question = validation_result.get('suggested_question')
            
            # STEP 5: Create order if confident BUY intent OR send clarifying question
            if intent.intent == "BUY":
                if analysis.requires_clarification and analysis.suggested_question:
                    # Send clarifying question to customer
                    await self._send_clarifying_question(
                        message_data, analysis.suggested_question
                    )
                    logger.info(f"❓ Sent clarifying question for message {message_id}")
                
                elif (analysis.extracted_products and 
                      intent.confidence >= settings.ai_confidence_threshold and
                      not analysis.requires_clarification):
                    # High confidence - create order directly
                    order_created = await self._create_simple_order(
                        message_data, analysis
                    )
                    if order_created:
                        logger.info(f"✅ Created order from message {message_id}")
                
                else:
                    logger.info(f"⚠️ BUY intent but insufficient confidence or no products matched for message {message_id}")
            
            # STEP 6: Update message with AI analysis
            analysis.processing_time_ms = int((time.time() - start_time) * 1000)
            
            await update_message_ai_data(
                self.database, message_id, analysis, self.distributor_id
            )
            
            logger.info(
                f"✅ Completed message {message_id} "
                f"(intent: {intent.intent}, confidence: {intent.confidence:.2f}, "
                f"products: {len(analysis.extracted_products)}, "
                f"time: {analysis.processing_time_ms}ms)"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to process message {message_id}: {e}")
            return None
    
    async def _get_simple_context(
        self, conversation_id: str, customer_id: str
    ) -> str:
        """
        Get simple conversation context (last 10 messages + recent orders).
        
        Much simpler than complex conversation memory system.
        """
        context_parts = []
        
        try:
            # Get recent messages (last 10)
            if conversation_id:
                recent_messages = await get_recent_messages_for_context(
                    self.database, conversation_id, self.distributor_id, limit=10
                )
                if recent_messages:
                    context_parts.append("Recent messages:")
                    for msg in recent_messages[-5:]:  # Last 5 messages
                        content = msg.get('content', '')[:100]  # First 100 chars
                        context_parts.append(f"- {content}")
            
            # Get recent orders (last 24 hours)
            if customer_id:
                recent_orders = await get_recent_orders(
                    self.database, customer_id, self.distributor_id, hours=24
                )
                if recent_orders:
                    context_parts.append("Recent orders:")
                    for order in recent_orders[:3]:  # Last 3 orders
                        context_parts.append(f"- Order {order.get('order_number', 'N/A')}")
        
        except Exception as e:
            logger.warning(f"Failed to get context: {e}")
        
        return "\n".join(context_parts) if context_parts else "No previous context"
    
    async def _analyze_with_openai(
        self, content: str, context: str
    ) -> Optional[tuple[MessageIntent, List[ExtractedProduct]]]:
        """
        Analyze message with OpenAI to get intent and products using structured JSON output.
        
        Let OpenAI handle all the language understanding and extraction.
        """
        try:
            # Give product catalog context if available
            catalog_context = ""
            try:
                catalog = await fetch_product_catalog(self.database, self.distributor_id)
                if catalog:
                    product_names = [p.product_name for p in catalog[:10]]  # Top 10 products
                    catalog_context = f"\n\nAVAILABLE PRODUCTS (sample): {', '.join(product_names)}"
            except:
                pass
            
            prompt = f"""
            Analyze this customer message and return a JSON response:
            
            MESSAGE: "{content}"
            
            CONTEXT: {context}{catalog_context}
            
            Return ONLY valid JSON in this exact format:
            {{
              "intent": "BUY",
              "confidence": 0.85,
              "reasoning": "Customer expressing purchase intent",
              "products": [
                {{
                  "name": "aceite de canola",
                  "quantity": 1,
                  "unit": "litro",
                  "original_text": "un litro de aceite de canola"
                }}
              ]
            }}
            
            IMPORTANT:
            - For Spanish numbers like "un/una" use quantity: 1
            - Extract the exact product name as mentioned
            - Include unit if mentioned (litro, botella, kilo, etc)
            - If no products for BUY intent, use empty products array
            """
            
            result = await streamlined_agent.run(prompt, deps=self.deps)
            response_text = str(result.data)
            
            # Try to parse as JSON first (OpenAI should return valid JSON)
            try:
                import json
                # Find JSON in response (handle cases where there's extra text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    data = json.loads(json_str)
                    
                    # Create intent from JSON
                    intent = MessageIntent(
                        intent=data.get('intent', 'OTHER'),
                        confidence=float(data.get('confidence', 0.5)),
                        reasoning=data.get('reasoning', 'AI analysis')
                    )
                    
                    # Create products from JSON
                    products = []
                    if data.get('products'):
                        for p in data['products']:
                            products.append(ExtractedProduct(
                                product_name=p.get('name', ''),
                                quantity=int(p.get('quantity', 1)),
                                unit=p.get('unit'),
                                original_text=p.get('original_text', content),
                                confidence=float(p.get('confidence', intent.confidence))
                            ))
                    
                    return intent, products
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response, falling back to simple parsing: {e}")
            
            # Fallback to simple parsing if JSON fails
            intent = self._parse_intent(response_text, content)
            products = self._parse_products_simple(content) if intent.intent == "BUY" else []
            
            return intent, products
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return None
    
    def _parse_products_simple(self, content: str) -> List[ExtractedProduct]:
        """
        Simple fallback product extraction - minimal, reliable parsing.
        Let OpenAI do the heavy lifting, this is just a safety net.
        """
        products = []
        content_lower = content.lower()
        
        # Basic product keywords (just essentials)
        basic_products = {
            'aceite': 'aceite',
            'agua': 'agua embotellada',
            'leche': 'leche',
            'cerveza': 'cerveza',
            'coca cola': 'coca cola',
            'queso': 'queso',
            'pan': 'pan',
            'arroz': 'arroz',
            'frijoles': 'frijoles',
            'huevos': 'huevos'
        }
        
        # Simple Spanish numbers
        spanish_numbers = {
            'un': 1, 'una': 1, 'uno': 1,
            'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
            'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
            'media docena': 6, 'docena': 12
        }
        
        # Simple units
        units = ['litro', 'litros', 'botella', 'botellas', 'kilo', 'kilos', 'paquete', 'paquetes']
        
        # Try to find basic products
        for keyword, product_name in basic_products.items():
            if keyword in content_lower:
                quantity = 1
                unit = None
                
                # Look for quantity before the product
                words = content_lower.split()
                for i, word in enumerate(words):
                    if keyword in word:
                        # Check 3 words before for quantity
                        for j in range(max(0, i-3), i):
                            # Check for Spanish numbers
                            if words[j] in spanish_numbers:
                                quantity = spanish_numbers[words[j]]
                                break
                            # Check for numeric
                            try:
                                quantity = int(words[j])
                                break
                            except ValueError:
                                continue
                        
                        # Check for unit after product
                        for j in range(i+1, min(i+3, len(words))):
                            if words[j] in units:
                                unit = words[j].rstrip('s')  # Remove plural
                                break
                        break
                
                products.append(ExtractedProduct(
                    product_name=product_name,
                    quantity=quantity,
                    unit=unit,
                    original_text=content,
                    confidence=0.7  # Lower confidence for simple parsing
                ))
        
        return products
    
    def _parse_intent(self, response: str, content: str) -> MessageIntent:
        """Parse intent from OpenAI response with improved Spanish greeting detection."""
        
        content_lower = content.lower().strip()
        
        # FIRST: Check for greetings (most common case)
        greeting_words = [
            "hola", "buenos días", "buenas tardes", "buenas noches", 
            "buen día", "hi", "hello", "hey", "saludos", "que tal",
            "como estas", "como está", "good morning", "good afternoon",
            "buendia", "buenosdias"
        ]
        
        if any(greeting in content_lower for greeting in greeting_words):
            return MessageIntent(
                intent="OTHER",
                confidence=0.75,
                reasoning="Customer greeting or general conversation"
            )
        
        # SECOND: Check for clear purchase intent  
        buy_words = ["quiero", "necesito", "pedido", "order", "comprar", "me das", "vendeme"]
        if any(word in content_lower for word in buy_words):
            return MessageIntent(
                intent="BUY",
                confidence=0.85,
                reasoning="Customer expressing purchase intent"
            )
        
        # THIRD: Check for questions about products/prices
        question_words = ["precio", "catalogo", "cuanto", "cuesta", "tienes", "hay", "menu", "lista"]
        if any(word in content_lower for word in question_words) or content.endswith('?'):
            return MessageIntent(
                intent="QUESTION", 
                confidence=0.8,
                reasoning="Customer asking about products/services"
            )
        
        # FOURTH: Check for complaints
        complaint_words = ["problema", "queja", "mal", "error", "equivocado", "reclamo"]
        if any(word in content_lower for word in complaint_words):
            return MessageIntent(
                intent="COMPLAINT",
                confidence=0.8, 
                reasoning="Customer expressing dissatisfaction"
            )
        
        # DEFAULT: General conversation
        return MessageIntent(
            intent="OTHER",
            confidence=0.6,
            reasoning="General conversation or unclear intent"
        )
    
    def _parse_products_complex_DEPRECATED(self, response: str, content: str) -> List[ExtractedProduct]:
        """DEPRECATED: Complex Spanish product extraction - replaced by OpenAI-first approach."""
        
        products = []
        
        # Comprehensive product keywords based on our catalog
        product_keywords = {
            # Beverages
            'agua embotellada': 'agua embotellada',
            'agua': 'agua embotellada',
            'water': 'agua embotellada',
            'coca cola': 'coca cola',
            'coca': 'coca cola',
            'cola': 'coca cola',
            'coke': 'coca cola',
            'pepsi': 'pepsi',
            'jugo de naranja': 'jugo de naranja',
            'jugo naranja': 'jugo de naranja',
            'zumo naranja': 'jugo de naranja', 
            'orange juice': 'jugo de naranja',
            'red bull': 'red bull',
            'energética': 'red bull',
            'energy drink': 'red bull',
            'cerveza': 'cerveza corona',
            'corona': 'cerveza corona',
            'beer': 'cerveza corona',
            'café molido': 'café molido',
            'café': 'café molido',
            'coffee': 'café molido',
            
            # Cooking & Oils
            'aceite de canola': 'aceite de canola',
            'aceite canola': 'aceite de canola',
            'canola oil': 'aceite de canola',
            'aceite de oliva': 'aceite de oliva',
            'aceite oliva': 'aceite de oliva',
            'olive oil': 'aceite de oliva',
            'aceite extra virgen': 'aceite de oliva',
            'aceite': 'aceite',  # Generic fallback
            
            # Dairy Products
            'leche entera': 'leche entera',
            'leche': 'leche entera',
            'milk': 'leche entera',
            'queso fresco': 'queso fresco',
            'queso': 'queso fresco',
            'cheese': 'queso fresco',
            'yogurt natural': 'yogurt natural',
            'yogurt': 'yogurt natural',
            'mantequilla': 'mantequilla',
            'butter': 'mantequilla',
            'huevos': 'huevos',
            'eggs': 'huevos',
            
            # Snacks
            'papas fritas': 'papas fritas',
            'papas': 'papas fritas',
            'chips': 'papas fritas',
            'frituras': 'papas fritas',
            'galletas de chocolate': 'galletas de chocolate',
            'galletas': 'galletas de chocolate',
            'cookies': 'galletas de chocolate',
            'nueces mixtas': 'nueces mixtas',
            'nueces': 'nueces mixtas',
            'nuts': 'nueces mixtas',
            'crackers': 'crackers',
            'galletas saladas': 'crackers',
            
            # Frozen Foods
            'helado de vainilla': 'helado de vainilla',
            'helado': 'helado de vainilla',
            'ice cream': 'helado de vainilla',
            'verduras congeladas': 'verduras congeladas',
            'verduras': 'verduras congeladas',
            'vegetables': 'verduras congeladas',
            'pizza congelada': 'pizza congelada',
            'pizza': 'pizza congelada',
            'fresas congeladas': 'fresas congeladas',
            'fresas': 'fresas congeladas',
            'strawberries': 'fresas congeladas',
            
            # Bakery & Grains
            'pan integral': 'pan integral',
            'pan': 'pan integral',
            'bread': 'pan integral',
            'arroz blanco': 'arroz blanco',
            'arroz': 'arroz blanco',
            'rice': 'arroz blanco',
            
            # Canned & Others
            'atún': 'atún',
            'tuna': 'atún',
            'frijoles negros': 'frijoles negros',
            'frijoles': 'frijoles negros',
            'beans': 'frijoles negros',
            'detergente líquido': 'detergente líquido',
            'detergente': 'detergente líquido',
            'detergent': 'detergente líquido',
            'azúcar': 'azúcar blanca',
            'sugar': 'azúcar blanca'
        }
        
        # Spanish number recognition
        spanish_numbers = {
            'un': 1, 'una': 1, 'uno': 1,
            'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
            'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
            'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15,
            'veinte': 20, 'treinta': 30, 'cuarenta': 40, 'cincuenta': 50
        }
        
        # Spanish unit recognition
        spanish_units = {
            'litro': 'litro', 'litros': 'litro', 'l': 'litro',
            'botella': 'botella', 'botellas': 'botella',
            'lata': 'lata', 'latas': 'lata',
            'paquete': 'paquete', 'paquetes': 'paquete',
            'envase': 'envase', 'envases': 'envase',
            'bolsa': 'bolsa', 'bolsas': 'bolsa',
            'caja': 'caja', 'cajas': 'caja',
            'barra': 'barra', 'barras': 'barra',
            'docena': 'docena', 'docenas': 'docena',
            'kilo': 'kg', 'kilos': 'kg', 'kg': 'kg', 'kilogramo': 'kg', 'kilogramos': 'kg',
            'gramo': 'g', 'gramos': 'g', 'g': 'g',
            'pieza': 'pieza', 'piezas': 'pieza', 'unidad': 'unidad', 'unidades': 'unidad'
        }
        
        content_lower = content.lower()
        words = content_lower.split()
        
        # Enhanced product matching with compound names
        found_products = []
        
        # Sort keywords by length (longest first) to match compound names first
        sorted_keywords = sorted(product_keywords.keys(), key=len, reverse=True)
        
        for keyword in sorted_keywords:
            if keyword in content_lower:
                # Avoid duplicate shorter matches within longer ones
                overlaps = False
                for found in found_products:
                    if keyword in found['keyword'] or found['keyword'] in keyword:
                        overlaps = True
                        break
                
                if not overlaps:
                    found_products.append({
                        'keyword': keyword,
                        'product_name': product_keywords[keyword],
                        'start_pos': content_lower.find(keyword)
                    })
        
        # Extract quantity and unit for each found product
        for found in found_products:
            keyword = found['keyword']
            product_name = found['product_name']
            start_pos = found['start_pos']
            
            # Find quantity and unit near the product
            quantity = 1
            unit = None
            
            # Look for quantity in the text around the product
            keyword_words = keyword.split()
            for i, word in enumerate(words):
                if any(kw in word for kw in keyword_words):
                    # Search for quantity in the 3 words before the product
                    search_range = range(max(0, i-3), i)
                    for j in search_range:
                        search_word = words[j]
                        
                        # Check Spanish numbers
                        if search_word in spanish_numbers:
                            quantity = spanish_numbers[search_word]
                            break
                        
                        # Check numeric digits
                        try:
                            potential_qty = int(search_word)
                            if 1 <= potential_qty <= 100:  # Reasonable quantity range
                                quantity = potential_qty
                                break
                        except ValueError:
                            continue
                    
                    # Search for unit in the 2 words before and after the product
                    unit_search_range = list(range(max(0, i-2), i)) + list(range(i+1, min(len(words), i+3)))
                    for j in unit_search_range:
                        search_word = words[j]
                        if search_word in spanish_units:
                            unit = spanish_units[search_word]
                            break
                    
                    break
            
            # Create the extracted product
            product = ExtractedProduct(
                product_name=product_name,
                quantity=quantity,
                unit=unit,
                original_text=content,
                confidence=0.85  # Higher confidence for enhanced extraction
            )
            products.append(product)
        
        return products
    
    async def _intelligent_product_validation(
        self, products: List[ExtractedProduct], original_message: str, conversation_id: str
    ) -> Dict[str, Any]:
        """
        Intelligent product validation using status-based workflow.
        
        Products start as "draft", move to "pending" if clarification needed,
        and become "confirmed" when matched with high confidence.
        
        Args:
            products: List of extracted products to validate
            original_message: Original customer message
            conversation_id: Conversation ID for context
            
        Returns:
            Dict with validated_products, requires_clarification, suggested_question
        """
        try:
            # Get product catalog from database
            catalog_models = await fetch_product_catalog(
                self.database, self.distributor_id, active_only=True
            )
            
            if not catalog_models:
                logger.warning("No catalog available for validation")
                # Keep products as draft without catalog
                return {
                    'validated_products': products,
                    'requires_clarification': False,
                    'suggested_question': None
                }
            
            # Convert catalog models to dictionaries for the matcher
            catalog_dicts = []
            for product in catalog_models:
                catalog_dicts.append({
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'unit': product.unit,
                    'unit_price': float(product.unit_price),
                    'stock_quantity': product.stock_quantity,
                    'in_stock': product.in_stock,
                    'minimum_order_quantity': product.minimum_order_quantity,
                    'active': product.active,
                    'brand': product.brand,
                    'category': product.category,
                    'size_variants': product.size_variants,
                    'aliases': product.aliases,
                    'keywords': product.keywords,
                    'ai_training_examples': product.ai_training_examples,
                    'common_misspellings': product.common_misspellings,
                    'seasonal_patterns': product.seasonal_patterns
                })
            
            validated_products = []
            overall_requires_clarification = False
            suggested_questions = []
            
            # Process each extracted product with status-based workflow
            for extracted_product in products:
                # Use our intelligent matcher to find matches
                match_result = self.product_matcher.match_products(
                    extracted_product.product_name, 
                    catalog_dicts
                )
                
                logger.info(
                    f"Product matching result for '{extracted_product.product_name}': "
                    f"confidence_level={match_result.confidence_level}, "
                    f"matches={len(match_result.matches)}"
                )
                
                if match_result.confidence_level == "HIGH":
                    # High confidence - mark as confirmed
                    best_match = match_result.best_match
                    extracted_product.status = "confirmed"
                    extracted_product.matched_product_id = best_match.product_id
                    extracted_product.matched_product_name = best_match.product_name
                    extracted_product.validation_notes = f"Matched with {best_match.confidence:.0%} confidence"
                    # Update unit if catalog has better info
                    if best_match.unit and not extracted_product.unit:
                        extracted_product.unit = best_match.unit
                    validated_products.append(extracted_product)
                    
                elif match_result.confidence_level in ["MEDIUM", "LOW"]:
                    # Medium/Low confidence - mark as pending and ask for clarification
                    extracted_product.status = "pending"
                    overall_requires_clarification = True
                    
                    if match_result.best_match:
                        extracted_product.matched_product_id = match_result.best_match.product_id
                        extracted_product.matched_product_name = match_result.best_match.product_name
                        extracted_product.validation_notes = f"Uncertain match ({match_result.best_match.confidence:.0%})"
                    
                    if match_result.suggested_question:
                        extracted_product.clarification_asked = match_result.suggested_question
                        suggested_questions.append(match_result.suggested_question)
                    
                    validated_products.append(extracted_product)
                
                else:  # NONE
                    # No matches found - mark as pending and need clarification
                    extracted_product.status = "pending"
                    extracted_product.validation_notes = "No catalog match found"
                    overall_requires_clarification = True
                    
                    if match_result.suggested_question:
                        extracted_product.clarification_asked = match_result.suggested_question
                        suggested_questions.append(match_result.suggested_question)
                    
                    validated_products.append(extracted_product)
            
            # Combine multiple questions into one coherent message
            combined_question = None
            if suggested_questions:
                if len(suggested_questions) == 1:
                    combined_question = suggested_questions[0]
                else:
                    combined_question = "Tengo algunas preguntas sobre tu pedido:\n\n" + "\n".join(
                        f"• {q}" for q in suggested_questions[:3]  # Limit to 3 questions
                    )
            
            return {
                'validated_products': validated_products,
                'requires_clarification': overall_requires_clarification,
                'suggested_question': combined_question
            }
            
        except Exception as e:
            logger.error(f"Intelligent product validation failed: {e}")
            # Fallback to original products if validation fails
            return {
                'validated_products': products,
                'requires_clarification': False,
                'suggested_question': None
            }
    
    async def _send_clarifying_question(
        self, message_data: Dict[str, Any], question: str
    ) -> bool:
        """
        Send a clarifying question back to the customer.
        
        Args:
            message_data: Original message data with conversation info
            question: Clarifying question to send
            
        Returns:
            True if question was sent successfully
        """
        try:
            conversation_id = message_data.get('conversation_id')
            if not conversation_id:
                logger.error("No conversation ID available to send clarifying question")
                return False
            
            # Create a response message in the database
            # Note: In a real implementation, this would integrate with WhatsApp Business API
            # For now, we'll store it as a message from the distributor
            
            from tools.supabase_tools import create_distributor_message
            
            await create_distributor_message(
                database=self.database,
                conversation_id=conversation_id,
                content=question,
                distributor_id=self.distributor_id,
                message_type='TEXT'
            )
            
            logger.info(f"✅ Sent clarifying question to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send clarifying question: {e}")
            return False
    
    async def _create_simple_order(
        self, message_data: Dict[str, Any], analysis: MessageAnalysis
    ) -> bool:
        """
        Create order from confirmed products only.
        
        Only products with status="confirmed" will be included in the order.
        """
        try:
            customer_id = message_data.get('customer_id')
            if not customer_id or not analysis.extracted_products:
                return False
            
            # Filter for confirmed products only
            confirmed_products = [p for p in analysis.extracted_products if p.status == "confirmed"]
            
            if not confirmed_products:
                logger.info("No confirmed products to create order")
                return False
            
            # Convert ExtractedProduct to OrderProduct
            order_products = []
            for extracted in confirmed_products:
                order_product = OrderProduct(
                    product_name=extracted.matched_product_name or extracted.product_name,
                    quantity=extracted.quantity,
                    unit=extracted.unit,
                    unit_price=None,  # Pricing handled elsewhere
                    line_price=None,
                    ai_confidence=extracted.confidence,
                    original_text=extracted.original_text,
                    matched_product_id=extracted.matched_product_id,
                    matching_confidence=extracted.confidence
                )
                order_products.append(order_product)
            
            # Create order
            order_creation = OrderCreation(
                customer_id=customer_id,
                distributor_id=self.distributor_id,
                conversation_id=message_data.get('conversation_id'),
                channel=message_data.get('channel', 'WHATSAPP'),
                products=order_products,
                delivery_date=None,
                additional_comment=None,
                ai_confidence=analysis.intent.confidence,
                source_message_ids=[message_data.get('id', '')]
            )
            
            order_id = await create_order(self.database, order_creation)
            return order_id is not None
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return False


def create_streamlined_order_agent_processor(
    database: DatabaseService, distributor_id: str
) -> StreamlinedOrderProcessor:
    """
    Factory function for streamlined processor.
    
    Much simpler than complex version - no product matcher needed.
    """
    return StreamlinedOrderProcessor(database, distributor_id)