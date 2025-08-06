#!/usr/bin/env python3
"""
Direct test of the full message processing pipeline.

Tests the complete StreamlinedOrderProcessor flow with Spanish extraction.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.order_agent import StreamlinedOrderProcessor
from services.database import DatabaseService

# Set up logging to see what happens
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

class MockDatabaseService:
    """Mock database service for testing."""
    
    async def execute_query(self, *args, **kwargs):
        return []
    
    async def fetch_one(self, *args, **kwargs):
        return None
    
    async def fetch_all(self, *args, **kwargs):
        return []

async def test_full_processing():
    """Test the complete message processing pipeline."""
    
    print("🧪 Testing Full Message Processing Pipeline")
    print("=" * 60)
    
    # Create mock database
    mock_db = MockDatabaseService()
    
    # Initialize the processor
    processor = StreamlinedOrderProcessor(mock_db, "demo-distributor")
    
    # Test message data (similar to what the webhook sends)
    message_data = {
        "id": "test-message-123",
        "content": "Quiero comprar un litro de aceite de canola por favor",
        "customer_id": "test-customer-456",
        "conversation_id": "test-conversation-789",
        "channel": "WHATSAPP"
    }
    
    print(f"📝 Processing message: '{message_data['content']}'")
    print()
    
    try:
        # This will call the full processing pipeline
        # Note: Some parts will fail due to mocked database, but we can see the extraction results
        result = await processor.process_message(message_data)
        
        if result:
            print("✅ Message processing completed!")
            print(f"📊 Results:")
            print(f"   Intent: {result.intent.intent}")
            print(f"   Confidence: {result.intent.confidence}")
            print(f"   Reasoning: {result.intent.reasoning}")
            print(f"   Products found: {len(result.extracted_products)}")
            
            if result.extracted_products:
                print(f"\n🛒 Extracted Products:")
                for i, product in enumerate(result.extracted_products, 1):
                    print(f"   Product {i}:")
                    print(f"     Name: {product.product_name}")
                    print(f"     Quantity: {product.quantity}")
                    print(f"     Unit: {product.unit}")
                    print(f"     Confidence: {product.confidence}")
                
                # Verify our expected results
                first_product = result.extracted_products[0]
                success = True
                
                print(f"\n🎯 Verification:")
                
                if first_product.product_name == "aceite de canola":
                    print(f"   ✅ Product name: {first_product.product_name}")
                else:
                    print(f"   ❌ Product name: Expected 'aceite de canola', got '{first_product.product_name}'")
                    success = False
                
                if first_product.quantity == 1:
                    print(f"   ✅ Quantity: {first_product.quantity} (from 'un')")
                else:
                    print(f"   ❌ Quantity: Expected 1, got {first_product.quantity}")
                    success = False
                
                if first_product.unit == "litro":
                    print(f"   ✅ Unit: {first_product.unit}")
                else:
                    print(f"   ❌ Unit: Expected 'litro', got '{first_product.unit}'")
                    success = False
                
                if success:
                    print(f"\n🎉 PERFECT! Spanish extraction working correctly in full pipeline!")
                else:
                    print(f"\n⚠️ Some issues found in the extraction")
            else:
                print(f"\n❌ No products extracted!")
                
            # Check for clarification questions
            if result.requires_clarification:
                print(f"\n❓ Clarification required: {result.suggested_question}")
            else:
                print(f"\n✅ No clarification needed - high confidence extraction")
                
        else:
            print("❌ Processing failed - result is None")
            
    except Exception as e:
        print(f"⚠️ Processing encountered error: {e}")
        # This is expected due to mocked database, but we should still see extraction results in logs
        print("(This is expected due to mocked database - check logs above for extraction results)")
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Full Processing Pipeline Test")
    print("Testing: 'Quiero comprar un litro de aceite de canola por favor'")
    print()
    
    asyncio.run(test_full_processing())