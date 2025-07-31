#!/usr/bin/env python3
"""
Test order creation with order_products to identify the insertion issue.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.database import DatabaseService
from schemas.order import OrderCreation, OrderProduct
from tools.supabase_tools import create_order

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def test_order_creation_with_products():
    """Test creating an order with products to see why order_products fail."""
    
    print("🧪 TESTING ORDER CREATION WITH PRODUCTS")
    print("=" * 60)
    
    db = DatabaseService()
    
    # Use the correct distributor and customer IDs from the real message
    distributor_id = "550e8400-e29b-41d4-a716-446655440000"
    customer_id = "d0ad369e-8d92-4b1b-80ed-2fda2bab9be0"
    conversation_id = "56d78925-2a57-4ff8-93dd-27e5557d0d8c"
    
    try:
        # Create a test order with products
        order_product = OrderProduct(
            product_name="aceite de canola",
            quantity=2,
            unit="litros",
            unit_price=None,
            line_price=None,
            ai_confidence=0.85,
            original_text="2 litros de aceite de canola",
            matched_product_id="229578f5-8d68-4cae-9e4c-4e96f82f2e3e",
            matching_confidence=0.90
        )
        
        order_creation = OrderCreation(
            customer_id=customer_id,
            distributor_id=distributor_id,
            conversation_id=conversation_id,
            channel="WHATSAPP",
            products=[order_product],
            delivery_date=None,
            additional_comment=None,
            ai_confidence=0.85,
            source_message_ids=["cf6e8df5-e3d8-4b58-8268-bb8cfefec18d"]
        )
        
        print("📋 Order Creation Data:")
        print(f"   Customer ID: {customer_id}")
        print(f"   Distributor ID: {distributor_id}")
        print(f"   Products: {len(order_creation.products)}")
        for i, p in enumerate(order_creation.products, 1):
            print(f"     {i}. {p.product_name} x{p.quantity} {p.unit or ''}")
            print(f"        Matched Product ID: {p.matched_product_id}")
            print(f"        AI Confidence: {p.ai_confidence}")
        print()
        
        print("🚀 Creating order...")
        order_id = await create_order(db, order_creation)
        
        if order_id:
            print(f"✅ Order created successfully: {order_id}")
            
            # Now check if order_products were created
            print("\n🔍 Checking order_products...")
            
            # Query order_products without distributor_id filter
            order_products = await db.execute_query(
                table='order_products',
                operation='select',
                filters={'order_id': order_id},
                distributor_id=None  # No distributor_id column in order_products
            )
            
            if order_products:
                print(f"✅ Found {len(order_products)} order_products:")
                for i, op in enumerate(order_products, 1):
                    print(f"   {i}. {op.get('product_name')} x{op.get('quantity')}")
                    print(f"      Order ID: {op.get('order_id')}")
                    print(f"      AI Confidence: {op.get('ai_confidence')}")
                    print(f"      Matched Product ID: {op.get('matched_product_id')}")
            else:
                print("❌ No order_products found!")
                print("This confirms the order_products insertion is failing.")
        else:
            print("❌ Order creation failed!")
        
        return order_id is not None
        
    except Exception as e:
        print(f"💥 Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the order creation test."""
    print("🚀 Order Products Creation Test")
    print("Testing order creation with products to debug insertion issues...")
    print()
    
    success = await test_order_creation_with_products()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎯 Test completed - check results above for order_products status")
    else:
        print("⚠️ Test failed - see error details above")

if __name__ == "__main__":
    asyncio.run(main())