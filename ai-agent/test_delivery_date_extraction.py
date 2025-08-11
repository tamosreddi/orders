#!/usr/bin/env python3
"""
Simple test script for delivery date extraction feature.

Tests the enhanced OpenAI message analysis with delivery date extraction.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from services.database import DatabaseService
from agents.order_agent import StreamlinedOrderProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test messages with various delivery date patterns
TEST_MESSAGES = [
    {
        "content": "Quiero 2 botellas de agua para mañana",
        "expected_date_pattern": "tomorrow",
        "description": "Tomorrow request"
    },
    {
        "content": "Necesito aceite de canola urgente para hoy",
        "expected_date_pattern": "today",
        "description": "Urgent today request"
    },
    {
        "content": "Dame 5 kilos de arroz para el viernes",
        "expected_date_pattern": "this Friday",
        "description": "Specific weekday"
    },
    {
        "content": "Lo necesito para la próxima semana",
        "expected_date_pattern": "next week",
        "description": "Next week request"
    },
    {
        "content": "Quiero 3 litros de leche",
        "expected_date_pattern": None,
        "description": "No delivery date mentioned"
    },
    {
        "content": "Para el 15 necesito pan y queso",
        "expected_date_pattern": "15th of month",
        "description": "Specific day of month"
    }
]

async def test_delivery_date_extraction():
    """Test delivery date extraction functionality."""
    
    logger.info("🧪 Testing Delivery Date Extraction")
    logger.info("=" * 50)
    
    try:
        # Create a mock database service
        database = DatabaseService()
        
        # Initialize the processor
        processor = StreamlinedOrderProcessor(
            database=database,
            distributor_id="test-distributor-123"
        )
        
        for i, test_case in enumerate(TEST_MESSAGES, 1):
            logger.info(f"\n🔍 Test {i}: {test_case['description']}")
            logger.info(f"Message: '{test_case['content']}'")
            logger.info(f"Expected: {test_case['expected_date_pattern'] or 'No date'}")
            logger.info("-" * 40)
            
            try:
                # Test just the OpenAI analysis part
                result = await processor._analyze_with_openai(
                    content=test_case['content'],
                    context="Test context"
                )
                
                if result:
                    intent, products, delivery_date = result
                    
                    logger.info(f"✅ Intent: {intent.intent}")
                    logger.info(f"✅ Confidence: {intent.confidence:.2f}")
                    logger.info(f"✅ Products: {len(products)}")
                    logger.info(f"✅ Delivery Date: {delivery_date or 'None'}")
                    
                    # Basic validation
                    if test_case['expected_date_pattern'] is None:
                        if delivery_date is None:
                            logger.info("✅ Correctly detected no delivery date")
                        else:
                            logger.warning(f"⚠️ Expected no date but got: {delivery_date}")
                    else:
                        if delivery_date:
                            logger.info(f"✅ Delivery date extracted: {delivery_date}")
                            
                            # Basic date format validation
                            try:
                                parsed_date = datetime.fromisoformat(delivery_date)
                                logger.info(f"✅ Date format valid: {parsed_date.strftime('%A, %B %d, %Y')}")
                            except ValueError:
                                logger.error(f"❌ Invalid date format: {delivery_date}")
                        else:
                            logger.warning(f"⚠️ Expected date pattern '{test_case['expected_date_pattern']}' but got None")
                else:
                    logger.error(f"❌ Analysis failed for test {i}")
                
            except Exception as e:
                logger.error(f"❌ Test {i} failed with error: {e}")
    
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        logger.info("Note: This test requires proper database configuration and OpenAI API key")
    
    logger.info("\n" + "=" * 50)
    logger.info("🎯 Delivery Date Extraction test completed!")
    logger.info("\nTo run this test properly, ensure:")
    logger.info("1. Environment variables are set (OPENAI_API_KEY, SUPABASE_URL, etc.)")
    logger.info("2. Virtual environment is activated")
    logger.info("3. All dependencies are installed")

if __name__ == "__main__":
    asyncio.run(test_delivery_date_extraction())