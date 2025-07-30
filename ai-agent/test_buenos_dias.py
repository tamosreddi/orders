#!/usr/bin/env python3
"""
Quick test to verify that "Buenos días" is correctly classified as OTHER intent.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, '.')

from agents.order_agent import StreamlinedOrderProcessor
from services.database import DatabaseService

async def test_buenos_dias():
    """Test that Buenos días is classified as OTHER intent."""
    
    # Create database service and processor
    distributor_id = os.getenv('DEMO_DISTRIBUTOR_ID')
    if not distributor_id:
        print("❌ DEMO_DISTRIBUTOR_ID not found in environment")
        return False
    
    db = DatabaseService()
    processor = StreamlinedOrderProcessor(db, distributor_id)
    
    # Test message data
    test_message = {
        'id': 'test-123',
        'content': 'Buenos días',
        'customer_id': 'test-customer-123',
        'conversation_id': 'test-conversation-123'
    }
    
    print(f"🧪 Testing message: '{test_message['content']}'")
    print(f"🏢 Using distributor: {distributor_id}")
    
    try:
        # Process the message
        result = await processor.process_message(test_message)
        
        if result is None:
            print("❌ Processing failed - no result returned")
            return False
        
        # Check the intent classification
        intent = result.intent.intent
        confidence = result.intent.confidence
        reasoning = result.intent.reasoning
        
        print(f"🤖 AI Analysis:")
        print(f"   Intent: {intent}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Reasoning: {reasoning}")
        print(f"   Processing time: {result.processing_time_ms}ms")
        
        # Verify it's classified as OTHER
        if intent == "OTHER":
            print("✅ SUCCESS: 'Buenos días' correctly classified as OTHER")
            return True
        else:
            print(f"❌ FAILED: Expected 'OTHER' but got '{intent}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔄 Testing Buenos días intent classification...")
    success = asyncio.run(test_buenos_dias())
    
    if success:
        print("\n🎉 Test PASSED - All fixes working correctly!")
        sys.exit(0)
    else:
        print("\n💥 Test FAILED - Issues remain")
        sys.exit(1)