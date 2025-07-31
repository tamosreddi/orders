#!/usr/bin/env python3
"""
FINAL Order Creation Test

Using ALL proper UUIDs - this should work!
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

async def test_final_order_creation():
    """Final test with ALL proper UUIDs."""
    
    print("🎯 FINAL ORDER CREATION TEST")
    print("=" * 60)
    
    # Create database service
    db = DatabaseService()
    
    # Use proper distributor UUID
    distributor_id = "69f73909-7190-4c39-b2d6-8c8066c8bea1"  # Default Distributor
    
    # Initialize processor with proper UUID
    processor = StreamlinedOrderProcessor(db, distributor_id)
    
    # Use REAL UUIDs from the successful message
    real_message_id = "983aa8d2-1ac5-450f-bc70-3e6901fabd29"
    real_conversation_id = "56d78925-2a57-4ff8-93dd-27e5557d0d8c"
    real_customer_id = "d0ad369e-8d92-4b1b-80ed-2fda2bab9be0"
    
    # Create the confirmed product
    confirmed_product = ExtractedProduct(
        product_name="aceite de canola",
        quantity=1,
        unit="litro",
        original_text="1 litro de aceite de canola",
        confidence=0.85,
        status="confirmed",  # ⭐ This should trigger order creation
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
    
    # Message data with ALL proper UUIDs
    message_data = {
        'id': real_message_id,
        'content': 'Hola quiero 1 litro de aceite de canola',
        'customer_id': real_customer_id,
        'conversation_id': real_conversation_id,
        'channel': 'WHATSAPP'
    }
    
    print("📋 ALL PROPER UUIDs:")
    print(f"   Distributor ID: {distributor_id}")
    print(f"   Message ID: {real_message_id}")
    print(f"   Customer ID: {real_customer_id}")
    print(f"   Conversation ID: {real_conversation_id}")
    print(f"   Product Status: {confirmed_product.status} ⭐")
    print()
    
    # The moment of truth!
    print("🚀 CREATING ORDER...")
    print("-" * 40)
    
    try:
        order_created = await processor._create_simple_order(message_data, analysis)
        
        if order_created:
            print("   🎉 SUCCESS! Order created successfully!")
            print()
            
            # Verify order in database
            print("🔍 VERIFYING ORDER IN DATABASE...")
            
            orders_query = """
            SELECT 
                id,
                status,
                channel,
                ai_source_message_id,
                ai_confidence,
                total_amount,
                created_at
            FROM orders 
            WHERE ai_source_message_id = %s
            ORDER BY created_at DESC
            """
            
            orders = await db.fetch_all(orders_query, [real_message_id])
            
            if orders:
                print(f"   ✅ Found {len(orders)} order(s)!")
                for order in orders:
                    print(f"     Order ID: {order['id']}")
                    print(f"     Status: {order['status']}")
                    print(f"     Channel: {order['channel']}")
                    print(f"     Total Amount: ${order['total_amount']}")
                    print(f"     Created: {order['created_at']}")
                
                # Check order products
                print("\n🍯 CHECKING ORDER PRODUCTS...")
                order_id = orders[0]['id']
                
                products_query = """
                SELECT 
                    product_name,
                    quantity,
                    unit,
                    unit_price,
                    line_price
                FROM order_products 
                WHERE order_id = %s
                """
                
                products = await db.fetch_all(products_query, [order_id])
                
                if products:
                    print(f"   ✅ Found {len(products)} product(s)!")
                    for product in products:
                        print(f"     Product: {product['product_name']}")
                        print(f"     Quantity: {product['quantity']} {product['unit'] or ''}")
                        print(f"     Price: ${product['unit_price'] or 'TBD'}")
                else:
                    print("   ❌ No order products found")
                    
            else:
                print("   ❌ No orders found in database!")
            
        else:
            print("   ❌ FAILED! Order creation returned False")
            
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    return order_created

async def main():
    """Run the final order creation test."""
    print("🏁 FINAL ORDER CREATION TEST")
    print("This should work with all proper UUIDs!")
    print()
    
    success = await test_final_order_creation()
    
    print("\n🏆 FINAL RESULT:")
    if success:
        print("✅ ORDER CREATION WORKING!")
        print("✅ Workflow Step 5 is functional")
        print("✅ Confirmed products → Orders pipeline working")
        print("\n🎯 Next Steps:")
        print("1. Test with real WhatsApp messages")
        print("2. Verify end-to-end workflow from webhook")
        print("3. Test conversational clarification flow")
    else:
        print("❌ ORDER CREATION STILL FAILING")
        print("❌ Need deeper debugging of create_order function")
        print("❌ May need schema fixes or missing data")

if __name__ == "__main__":
    asyncio.run(main())