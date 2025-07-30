"""
Streamlined Order Agent implementation for pilot testing.

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
    """Streamlined dependencies - no complex product matching."""
    database: DatabaseService
    distributor_id: str


# Simple system prompt for OpenAI
SYSTEM_PROMPT = """
You are an AI assistant for a B2B food distributor processing WhatsApp orders.

Your job is to analyze customer messages and extract order information.

INTENT CLASSIFICATION:
- BUY: Customer wants to purchase products
- QUESTION: Customer asking about products/services  
- COMPLAINT: Customer has an issue with order/service
- FOLLOW_UP: Customer referencing previous conversation
- OTHER: General conversation

PRODUCT EXTRACTION (for BUY intents):
Extract all products mentioned with quantities and units.

Respond with structured information that can be parsed.
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
        """Initialize the streamlined processor."""
        self.database = database
        self.distributor_id = distributor_id
        self.deps = StreamlinedAgentDeps(
            database=database,
            distributor_id=distributor_id
        )
        logger.info(f"Initialized StreamlinedOrderProcessor for distributor {distributor_id}")
    
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
            
            # STEP 4: Validate products against catalog (simplified)
            if products and intent.intent == "BUY":
                validated_products = await self._simple_product_validation(products)
                analysis.extracted_products = validated_products
            
            # STEP 5: Create order if confident BUY intent
            if (intent.intent == "BUY" and 
                analysis.extracted_products and 
                intent.confidence >= settings.ai_confidence_threshold):
                
                order_created = await self._create_simple_order(
                    message_data, analysis
                )
                if order_created:
                    logger.info(f"✅ Created order from message {message_id}")
            
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
        Analyze message with OpenAI to get intent and products.
        
        Single OpenAI call instead of complex workflow.
        """
        try:
            prompt = f"""
            Analyze this customer message:
            
            MESSAGE: "{content}"
            
            CONTEXT: {context}
            
            Please provide:
            1. INTENT: One of (BUY, QUESTION, COMPLAINT, FOLLOW_UP, OTHER)
            2. CONFIDENCE: Score from 0.0 to 1.0 
            3. REASONING: Why you chose this intent
            4. PRODUCTS: If BUY intent, list all products with quantities
            
            Format your response clearly so I can parse it.
            """
            
            result = await streamlined_agent.run(prompt, deps=self.deps)
            response_text = str(result.data).upper()
            
            # Simple parsing (in production, use structured output)
            intent = self._parse_intent(response_text, content)
            products = self._parse_products(response_text, content) if intent.intent == "BUY" else []
            
            return intent, products
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return None
    
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
    
    def _parse_products(self, response: str, content: str) -> List[ExtractedProduct]:
        """Extract products from message (simplified)."""
        
        products = []
        
        # Simple product detection (would use better NLP in production)
        product_keywords = {
            'agua': 'water',
            'leche': 'milk', 
            'cerveza': 'beer',
            'coca cola': 'coca cola',
            'coke': 'coca cola',
            'queso': 'cheese',
            'pan': 'bread',
            'botella': 'bottle',
            'caja': 'case'
        }
        
        content_lower = content.lower()
        
        for spanish, english in product_keywords.items():
            if spanish in content_lower:
                # Simple quantity extraction
                quantity = 1
                words = content_lower.split()
                
                # Look for numbers near the product
                for i, word in enumerate(words):
                    if spanish in word:
                        # Check 2 words before for quantity
                        for j in range(max(0, i-2), i):
                            try:
                                quantity = int(words[j])
                                break
                            except ValueError:
                                continue
                        break
                
                product = ExtractedProduct(
                    product_name=spanish,
                    quantity=quantity,
                    unit="units",
                    original_text=content,
                    confidence=0.7
                )
                products.append(product)
        
        return products
    
    async def _simple_product_validation(
        self, products: List[ExtractedProduct]
    ) -> List[ExtractedProduct]:
        """
        Simple product validation against catalog.
        
        Much simpler than complex fuzzy matching.
        """
        try:
            # Get product catalog
            catalog = await fetch_product_catalog(
                self.database, self.distributor_id, active_only=True
            )
            
            if not catalog:
                logger.warning("No catalog available for validation")
                return products  # Return as-is if no catalog
            
            # Simple name matching (case insensitive)
            catalog_names = [p.name.lower() for p in catalog]
            
            validated = []
            for product in products:
                # Check if product name exists in catalog
                product_name_lower = product.product_name.lower()
                
                # Direct match
                if product_name_lower in catalog_names:
                    product.confidence = min(product.confidence + 0.2, 1.0)
                
                # Partial match
                elif any(product_name_lower in name or name in product_name_lower 
                        for name in catalog_names):
                    product.confidence = min(product.confidence + 0.1, 1.0)
                
                validated.append(product)
            
            return validated
            
        except Exception as e:
            logger.error(f"Product validation failed: {e}")
            return products  # Return original if validation fails
    
    async def _create_simple_order(
        self, message_data: Dict[str, Any], analysis: MessageAnalysis
    ) -> bool:
        """
        Create order from analysis (simplified).
        
        No complex product matching - direct order creation.
        """
        try:
            customer_id = message_data.get('customer_id')
            if not customer_id or not analysis.extracted_products:
                return False
            
            # Convert ExtractedProduct to OrderProduct
            order_products = []
            for extracted in analysis.extracted_products:
                order_product = OrderProduct(
                    product_name=extracted.product_name,
                    quantity=extracted.quantity,
                    unit=extracted.unit,
                    unit_price=None,  # Pricing handled elsewhere
                    line_price=None,
                    ai_confidence=extracted.confidence,
                    original_text=extracted.original_text,
                    matched_product_id=None,  # Simplified - no complex matching
                    matching_confidence=None
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