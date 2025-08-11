#!/usr/bin/env python3
"""
Test temporal extraction with StreamlinedOrderProcessor
"""
import asyncio
import logging
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.order_agent import StreamlinedOrderProcessor
from services.database import DatabaseService
from dotenv import load_dotenv

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable OpenAI debug logging
logging.getLogger("openai").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)

load_dotenv()

async def test_temporal_extraction():
    """Test that 'mañana' is correctly extracted as tomorrow's date"""
    
    # Initialize database
    database = DatabaseService()
    await database.initialize()
    
    # Create processor
    distributor_id = "550e8400-e29b-41d4-a716-446655440000"
    processor = StreamlinedOrderProcessor(database, distributor_id)
    
    # Test message with temporal reference
    test_message = {
        'id': 'test-temporal-123',
        'conversation_id': 'conv-temporal-123',
        'customer_id': 'cust-temporal-123',
        'content': 'mándame dos aguas para mañana',
        'channel': 'WHATSAPP'
    }
    
    logger.info(f"🧪 Testing temporal extraction with message: '{test_message['content']}'")
    logger.info(f"📅 Today's date: {datetime.now().date()}")
    logger.info(f"📅 Expected tomorrow: {(datetime.now() + timedelta(days=1)).date()}")
    
    # Process message
    result = await processor.process_message(test_message)
    
    if result:
        logger.info(f"✅ Message processed successfully")
        logger.info(f"📊 Intent: {result.intent.intent} (confidence: {result.intent.confidence})")
        logger.info(f"📦 Products extracted: {len(result.extracted_products)}")
        logger.info(f"📅 Delivery date extracted: {result.delivery_date}")
        
        # Check if delivery date was extracted
        if result.delivery_date:
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            extracted_date = datetime.fromisoformat(result.delivery_date).date()
            
            if extracted_date == tomorrow:
                logger.info(f"✅ SUCCESS: Delivery date correctly extracted as tomorrow ({result.delivery_date})")
            else:
                logger.error(f"❌ FAIL: Delivery date {result.delivery_date} doesn't match expected tomorrow {tomorrow}")
        else:
            logger.error(f"❌ FAIL: No delivery date extracted from 'mañana'")
            
        # Show products
        for product in result.extracted_products:
            logger.info(f"  - {product.product_name}: {product.quantity} {product.unit or 'units'}")
    else:
        logger.error("❌ Failed to process message")
    
    await database.close()

if __name__ == "__main__":
    asyncio.run(test_temporal_extraction())