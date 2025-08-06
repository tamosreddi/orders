#!/usr/bin/env python3
"""
Test Order Creation with REAL UUIDs

Using the actual message that succeeded with confirmed products.
"""

import sys
import os
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.database import DatabaseService
from agents.order_agent import StreamlinedOrderProcessor
from schemas.message import MessageAnalysis, MessageIntent, ExtractedProduct

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def test_real_order_creation():
    """Test order creation with real UUIDs from the successful message."""
    
    print("🧪 TESTING ORDER CREATION WITH REAL UUIDs")
    print("=" * 60)
    
    # Create database service
    db = DatabaseService()
    
    # Initialize processor
    processor = StreamlinedOrderProcessor(db, "demo-distributor")
    
    # Use REAL UUIDs from the successful message
    real_message_id = "983aa8d2-1ac5-450f-bc70-3e6901fabd29"
    real_conversation_id = "56d78925-2a57-4ff8-93dd-27e5557d0d8c"
    real_customer_id = "d0ad369e-8d92-4b1b-80ed-2fda2bab9be0"
    
    # Create the same confirmed product from the database
    confirmed_product = ExtractedProduct(
        product_name="aceite de canola",
        quantity=1,
        unit="litro",
        original_text="1 litro de aceite de canola",
        confidence=0.85,
        status="confirmed",  # ⭐ Key field
        matched_product_id="229578f5-8d68-4cae-9e4c-4e96f82f2e3e",
        matched_product_name="Aceite de Canola 1L",
        validation_notes="Matched with 95% confidence"
    )
    
    intent = MessageIntent(
        intent="BUY",
        confidence=0.85,
        reasoning="Customer expressing purchase intent"
    )
    
    analysis = MessageAnalysis(
        message_id=real_message_id,
        intent=intent,
        extracted_products=[confirmed_product],
        processing_time_ms=1000
    )
    
    # Real message data with proper UUIDs
    message_data = {
        'id': real_message_id,
        'content': 'Hola quiero 1 litro de aceite de canola',
        'customer_id': real_customer_id,
        'conversation_id': real_conversation_id,
        'channel': 'WHATSAPP'
    }
    
    print("📋 Using REAL UUIDs:")
    print(f"   Message ID: {real_message_id}")
    print(f"   Customer ID: {real_customer_id}")
    print(f"   Conversation ID: {real_conversation_id}")
    print(f"   Product Status: {confirmed_product.status}")
    print()
    
    # Test order creation
    print("⚡ TESTING ORDER CREATION")
    print("-" * 40)
    
    try:
        order_created = await processor._create_simple_order(message_data, analysis)
        print(f"   Order Creation Result: {order_created}")
        
        if order_created:
            print("   ✅ SUCCESS! Order created successfully!")
            
            # Check if order appears in database
            print("\n🔍 Verifying order in database...")
            recent_orders_query = """
            SELECT 
                id,
                status,
                channel,
                ai_source_message_id,
                ai_confidence,
                created_at
            FROM orders 
            WHERE ai_source_message_id = %s
            """
            
            orders = await db.fetch_all(recent_orders_query, [real_message_id])
            
            if orders:
                print(f"   ✅ Found {len(orders)} order(s) in database!")
                for order in orders:
                    print(f"     Order ID: {order['id']}")
                    print(f"     Status: {order['status']}")
                    print(f"     Channel: {order['channel']}")
                    print(f"     AI Confidence: {order['ai_confidence']}")
            else:
                print("   ❌ No orders found in database")
            
        else:
            print("   ❌ FAILED! Order creation returned False")
            
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    return True

async def main():
    """Run the real order creation test."""
    print("🚀 Real Order Creation Test")
    print("Testing with actual UUIDs from successful message")
    print()
    
    success = await test_real_order_creation()
    
    if success:
        print("🎯 Test completed!")
        print("\nIf order creation succeeded:")
        print("✅ The workflow is working end-to-end")
        print("✅ Orders table should have new entries")
        print("✅ Step 5 (order creation) is functional")
        print("\nIf it failed:")
        print("❌ Need to debug the create_order function")
        print("❌ May be database schema issues")
    else:
        print("⚠️ Test failed.")

if __name__ == "__main__":
    asyncio.run(main())