"""
Simplified Autonomous Order Agent - TRULY SIMPLIFIED

Focused ONLY on business goal: Listen → Identify Orders → Create Orders

1. Intent classification - is this ORDER_RELATED?
2. OpenAI product extraction - extract any products from message
3. OpenAI product validation - verify products exist in catalog
4. Direct order creation - create order immediately
5. Update message - track processing

NO feature flags, NO smart consolidation, NO complex validation.
"""

from __future__ import annotations as _annotations

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import os
import openai
from config.settings import settings
from services.database import DatabaseService
from services.intent_classifier import intent_classifier, MessageIntent
from schemas.message import MessageAnalysis, ExtractedProduct
from tools.supabase_tools import update_message_ai_data
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SimplifiedAutonomousAgent:
    """
    Truly simplified agent for order capture only.
    
    Business Goal: Listen → Identify Orders → Create Orders
    
    Workflow:
    1. Intent classification - is this ORDER_RELATED?
    2. OpenAI product extraction - extract products from message
    3. OpenAI product validation - verify products exist in catalog
    4. Direct order creation - create order immediately
    5. Update message - track processing
    """
    
    def __init__(self, database: DatabaseService, distributor_id: str):
        self.database = database
        self.distributor_id = distributor_id
        self.intent_classifier = intent_classifier
        
        # Setup OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        logger.info(f"🤖 Initialized TRULY SimplifiedAutonomousAgent for distributor {distributor_id}")
    
    async def process_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process message through truly simplified workflow.
        
        Args:
            message_data: Message from webhook with id, content, customer_id, etc.
            
        Returns:
            Dict with success/failure info, None if should fallback to existing agent
        """
        start_time = time.time()
        message_id = message_data.get('id', '')
        content = message_data.get('content', '').strip()
        customer_id = message_data.get('customer_id', '')
        
        logger.info(f"🤖 TRULY SIMPLIFIED processing: '{content[:50]}...' (customer: {customer_id})")
        
        try:
            # STEP 1: Intent Classification - Is this ORDER_RELATED?
            intent_result = await self.intent_classifier.classify_message_intent(content)
            logger.info(f"🧠 Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
            
            if not intent_result.is_order_related:
                logger.info(f"📝 Not order-related, fallback to existing agent")
                return None  # Not an order, let existing agent handle
            
            # STEP 2: OpenAI Product Extraction
            logger.info(f"📦 Extracting products with OpenAI...")
            extracted_products = await self._extract_products_with_openai(content)
            
            if not extracted_products:
                logger.info(f"📦 No products extracted from ORDER_RELATED message")
                return None  # No products found, fallback
            
            logger.info(f"📦 Extracted {len(extracted_products)} products")
            
            # STEP 3: OpenAI Product Validation against Supabase catalog
            logger.info(f"✅ Validating products against catalog...")
            validated_products = await self._validate_products_in_database(extracted_products)
            
            if not validated_products:
                logger.info(f"❌ No valid products found in catalog")
                return None  # No valid products, fallback
            
            logger.info(f"✅ {len(validated_products)} products validated")
            
            # STEP 4: Direct Order Creation
            logger.info(f"🛒 Creating order...")
            order_id = await self._create_order_simple(
                customer_id, 
                message_data.get('conversation_id', ''), 
                validated_products,
                message_data.get('channel', 'WHATSAPP')
            )
            
            if not order_id:
                logger.error(f"❌ Order creation failed")
                return None  # Order creation failed, fallback
            
            # STEP 5: Update Message
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self._update_message_simple(message_id, order_id, intent_result, processing_time_ms)
            
            logger.info(f"🎉 Successfully created order {order_id} in {processing_time_ms}ms")
            
            return {
                'success': True,
                'order_id': order_id,
                'products_count': len(validated_products),
                'processing_time_ms': processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"❌ Simplified processing failed: {e}")
            return None  # Fallback on any error
    
    async def _extract_products_with_openai(self, content: str) -> List[ExtractedProduct]:
        """
        Extract products using OpenAI - works with ANY products, not just hardcoded ones.
        """
        try:
            # OpenAI extraction prompt
            extraction_prompt = f"""
            Analyze this customer message and extract product information.
            
            Customer message: "{content}"
            
            Return JSON with:
            {{
                "products": [
                    {{
                        "name": "product name",
                        "quantity": 1,
                        "unit": "unit or null",
                        "confidence": 0.8
                    }}
                ]
            }}
            
            Extract ALL products mentioned. Handle Spanish numbers (un/una=1, dos=2, tres=3, etc).
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1
            )
            
            # Parse OpenAI response
            import json
            try:
                result = json.loads(response.choices[0].message.content)
                products = result.get('products', [])
                
                # Convert to ExtractedProduct format
                extracted_products = []
                for product in products:
                    extracted_products.append(ExtractedProduct(
                        product_name=product.get('name', ''),
                        quantity=product.get('quantity', 1),
                        unit=product.get('unit'),
                        original_text=content,
                        confidence=product.get('confidence', 0.8)
                    ))
                
                return extracted_products
                
            except json.JSONDecodeError:
                logger.warning("OpenAI response was not valid JSON")
                return []
            
        except Exception as e:
            logger.warning(f"OpenAI product extraction failed: {e}")
            return []
    
    async def _validate_products_in_database(self, extracted_products: List[ExtractedProduct]) -> List[Dict[str, Any]]:
        """
        Use OpenAI to validate products against Supabase products table for this distributor.
        """
        try:
            # Get products from Supabase for this distributor
            products_data = await self.database.select_with_filters(
                table='products',
                filters={'distributor_id': self.distributor_id},
                select_fields=['id', 'name', 'price', 'unit', 'description']
            )
            
            if not products_data:
                logger.warning(f"No products found for distributor {self.distributor_id}")
                return []
            
            # Create product catalog text for OpenAI
            catalog_text = "Available products:\n"
            for product in products_data:
                catalog_text += f"- {product['name']} ({product.get('unit', 'unit')}) - ${product.get('price', 0)}\n"
            
            # Use OpenAI to match extracted products to catalog
            validation_prompt = f"""
            Customer requested these products:
            {[f"{p.quantity} {p.product_name}" for p in extracted_products]}
            
            {catalog_text}
            
            Match the customer's products to the available catalog. Return a JSON list with:
            [{"product_id": "123", "product_name": "matched_name", "quantity": 2, "price": 10.50, "unit": "kg"}]
            
            Only include products that have clear matches in the catalog.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0.1
            )
            
            # Parse OpenAI response
            import json
            try:
                validated_products = json.loads(response.choices[0].message.content)
                return validated_products if isinstance(validated_products, list) else []
            except json.JSONDecodeError:
                logger.warning("OpenAI response was not valid JSON")
                return []
            
        except Exception as e:
            logger.error(f"Product validation failed: {e}")
            return []
    
    async def _create_order_simple(
        self, 
        customer_id: str, 
        conversation_id: str, 
        validated_products: List[Dict[str, Any]],
        channel: str = 'WHATSAPP'
    ) -> Optional[str]:
        """
        Create order directly in database - no complex wrappers.
        """
        try:
            # Calculate total amount
            total_amount = sum(p.get('price', 0) * p.get('quantity', 0) for p in validated_products)
            
            # Create order
            order_data = {
                'customer_id': customer_id,
                'distributor_id': self.distributor_id,
                'conversation_id': conversation_id,
                'channel': channel,
                'status': 'PENDING',
                'total_amount': total_amount,
                'order_source': 'AUTONOMOUS_AGENT'
            }
            
            order_result = await self.database.insert_single('orders', order_data)
            if not order_result or 'id' not in order_result:
                return None
                
            order_id = order_result['id']
            
            # Create order products
            for product in validated_products:
                product_data = {
                    'order_id': order_id,
                    'product_id': product.get('product_id'),
                    'quantity': product.get('quantity', 1),
                    'unit_price': product.get('price', 0),
                    'total_price': product.get('price', 0) * product.get('quantity', 1)
                }
                
                await self.database.insert_single('order_products', product_data)
            
            logger.info(f"Created order {order_id} with {len(validated_products)} products")
            return order_id
            
        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            return None
    
    async def _update_message_simple(
        self, message_id: str, order_id: str, intent_result, processing_time_ms: int
    ) -> None:
        """Update message with simplified processing signature."""
        try:
            # Create simple MessageAnalysis for database update
            analysis = MessageAnalysis(
                message_id=message_id,
                intent=intent_result,
                extracted_products=[],  # Products handled by order creation
                customer_notes=None,
                delivery_date=None,
                processing_time_ms=processing_time_ms
            )
            
            # Add simple processing signature
            processing_signature = {
                'agent_type': 'TRULY_SIMPLIFIED_AUTONOMOUS',
                'processing_time_ms': processing_time_ms,
                'created_order_id': order_id,
                'success': True
            }
            
            # Update message
            await update_message_ai_data(
                self.database, message_id, analysis, self.distributor_id,
                additional_data={'autonomous_processing': processing_signature}
            )
            
        except Exception as e:
            logger.error(f"Failed to update message: {e}")


# Factory function for easy integration with existing agent factory
def create_simplified_autonomous_agent(
    database: DatabaseService, distributor_id: str
) -> SimplifiedAutonomousAgent:
    """Create truly simplified autonomous agent."""
    return SimplifiedAutonomousAgent(database, distributor_id)