#!/usr/bin/env python3
"""
Debug Order Creation Issue

Trace exactly why confirmed products aren't creating orders.
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
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def debug_order_creation():
    """Debug why orders aren't being created from confirmed products."""
    
    print("🔍 DEBUGGING ORDER CREATION ISSUE")
    print("=" * 60)
    
    # Create database service
    db = DatabaseService()
    
    # Initialize processor
    processor = StreamlinedOrderProcessor(db, "demo-distributor")
    
    # Create a realistic message analysis with confirmed product
    # (Simulating what should happen after the recent successful test)
    confirmed_product = ExtractedProduct(
        product_name="aceite de canola",
        quantity=1,
        unit="litro",
        original_text="1 litro de aceite de canola",
        confidence=0.85,
        status="confirmed",  # ⭐ This is the key field
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
        message_id="test-debug-order-creation",
        intent=intent,
        extracted_products=[confirmed_product],
        processing_time_ms=1000
    )
    
    # Simulate message data 
    message_data = {
        'id': 'test-debug-order-creation',
        'content': 'Hola quiero 1 litro de aceite de canola',
        'customer_id': 'test-customer-456',
        'conversation_id': 'test-conversation-789',
        'channel': 'WHATSAPP'
    }
    
    print("📝 Test Setup:")
    print(f"   Message: '{message_data['content']}'")
    print(f"   Intent: {intent.intent} ({intent.confidence:.2f})")
    print(f"   Products: {len(analysis.extracted_products)}")
    print(f"   Product Status: {confirmed_product.status} ⭐")
    print(f"   Product Confidence: {confirmed_product.confidence}")
    print()
    
    # STEP 1: Test the _create_simple_order method directly
    print("🧪 STEP 1: Testing _create_simple_order directly")
    print("-" * 40)
    
    try:
        order_created = await processor._create_simple_order(message_data, analysis)
        print(f"   Result: {order_created}")
        
        if order_created:
            print("   ✅ Order creation succeeded!")
        else:
            print("   ❌ Order creation failed!")
            
    except Exception as e:
        print(f"   💥 Exception in _create_simple_order: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # STEP 2: Check what's inside the analysis.extracted_products
    print("🔬 STEP 2: Analyzing ExtractedProduct object")
    print("-" * 40)
    
    for i, product in enumerate(analysis.extracted_products):
        print(f"   Product {i+1}:")
        print(f"     Type: {type(product)}")
        print(f"     Status attribute exists: {hasattr(product, 'status')}")
        if hasattr(product, 'status'):
            print(f"     Status value: '{product.status}'")
        print(f"     All attributes: {dir(product)}")
        print(f"     Product dict: {product.dict() if hasattr(product, 'dict') else 'No dict method'}")
        print()
    
    # STEP 3: Check filtering logic
    print("🎯 STEP 3: Testing confirmed products filtering")  
    print("-" * 40)
    
    confirmed_products = [p for p in analysis.extracted_products if p.status == "confirmed"]
    print(f"   Total products: {len(analysis.extracted_products)}")
    print(f"   Products with status='confirmed': {len(confirmed_products)}")
    
    if not confirmed_products:
        print("   ❌ NO CONFIRMED PRODUCTS FOUND!")
        print("   This is why no orders are created.")
        
        # Debug each product status
        for i, product in enumerate(analysis.extracted_products):
            print(f"   Product {i+1} status: '{getattr(product, 'status', 'NO STATUS ATTR')}'")
    else:
        print("   ✅ Confirmed products found, should create order")
    
    print()
    
    # STEP 4: Check recent database state
    print("📊 STEP 4: Checking current database state")
    print("-" * 40)
    
    try:
        # Check orders table
        orders_query = "SELECT COUNT(*) as order_count FROM orders WHERE created_at > NOW() - INTERVAL '1 day'"
        orders_result = await db.fetch_one(orders_query)
        print(f"   Recent orders in DB: {orders_result['order_count'] if orders_result else 'N/A'}")
        
        # Check messages with confirmed products
        messages_query = """
        SELECT COUNT(*) as msg_count 
        FROM messages 
        WHERE ai_extracted_products::text LIKE '%"status":"confirmed"%'
            AND created_at > NOW() - INTERVAL '1 day'
        """
        messages_result = await db.fetch_one(messages_query)
        print(f"   Messages with confirmed products: {messages_result['msg_count'] if messages_result else 'N/A'}")
        
    except Exception as e:
        print(f"   Database check failed: {e}")
    
    return True

async def main():
    """Run the order creation debugging."""
    print("🚀 Order Creation Debug Session")
    print("Investigating why confirmed products don't create orders")
    print()
    
    success = await debug_order_creation()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎯 Debug session completed!")
        print("\nExpected findings:")
        print("1. _create_simple_order method execution result")
        print("2. ExtractedProduct.status attribute analysis") 
        print("3. Filtering logic verification")
        print("4. Current database state")
    else:
        print("⚠️ Debug session failed.")
    
    print("\n💡 Next steps based on findings:")
    print("1. Fix any issues found in order creation logic")
    print("2. Test complete workflow end-to-end")
    print("3. Verify orders and order_products tables populated correctly")

if __name__ == "__main__":
    asyncio.run(main())