#!/usr/bin/env python3
"""
Quick test script for the enhanced order agent with intelligent product matching.

Tests the complete workflow from message processing to product validation.
"""

import asyncio
import logging
from services.database import DatabaseService
from agents.order_agent import StreamlinedOrderProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_enhanced_agent():
    """Test the enhanced agent with mock message data."""
    
    try:
        # Initialize components
        database = DatabaseService()
        distributor_id = '550e8400-e29b-41d4-a716-446655440000'
        
        processor = StreamlinedOrderProcessor(database, distributor_id)
        
        # Test message 1: High confidence match
        message_data_1 = {
            'id': 'test-msg-1',
            'content': 'Quiero 5 botellas de agua',
            'customer_id': 'test-customer-1',
            'conversation_id': 'test-conv-1',
            'channel': 'WHATSAPP'
        }
        
        logger.info("🧪 Testing high confidence product match: 'Quiero 5 botellas de agua'")
        result_1 = await processor.process_message(message_data_1)
        
        if result_1:
            logger.info(f"✅ Result 1: Intent={result_1.intent.intent}, Products={len(result_1.extracted_products)}, Clarification={result_1.requires_clarification}")
            if result_1.extracted_products:
                for product in result_1.extracted_products:
                    logger.info(f"  - Product: {product.product_name} (confidence: {product.confidence:.2f})")
        else:
            logger.error("❌ Test 1 failed - no result returned")
        
        # Test message 2: Medium confidence match requiring clarification
        message_data_2 = {
            'id': 'test-msg-2',
            'content': 'Necesito algunos refrescos',
            'customer_id': 'test-customer-2',
            'conversation_id': 'test-conv-2',
            'channel': 'WHATSAPP'
        }
        
        logger.info("🧪 Testing medium confidence product match: 'Necesito algunos refrescos'")
        result_2 = await processor.process_message(message_data_2)
        
        if result_2:
            logger.info(f"✅ Result 2: Intent={result_2.intent.intent}, Products={len(result_2.extracted_products)}, Clarification={result_2.requires_clarification}")
            if result_2.suggested_question:
                logger.info(f"  - Suggested question: {result_2.suggested_question}")
        else:
            logger.error("❌ Test 2 failed - no result returned")
        
        # Test message 3: No product match
        message_data_3 = {
            'id': 'test-msg-3',
            'content': 'Quiero comprar unos zapatos',
            'customer_id': 'test-customer-3',
            'conversation_id': 'test-conv-3',
            'channel': 'WHATSAPP'
        }
        
        logger.info("🧪 Testing no product match: 'Quiero comprar unos zapatos'")
        result_3 = await processor.process_message(message_data_3)
        
        if result_3:
            logger.info(f"✅ Result 3: Intent={result_3.intent.intent}, Products={len(result_3.extracted_products)}, Clarification={result_3.requires_clarification}")
            if result_3.suggested_question:
                logger.info(f"  - Suggested question: {result_3.suggested_question}")
        else:
            logger.error("❌ Test 3 failed - no result returned")
        
        logger.info("🎉 Enhanced agent testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhanced_agent())