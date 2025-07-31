#!/usr/bin/env python3
"""
Check if orders are being created from confirmed products.
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.database import DatabaseService

async def check_recent_orders():
    """Check for recent orders in the database."""
    print("🔍 CHECKING RECENT ORDERS")
    print("=" * 50)
    
    db = DatabaseService()
    
    # Check orders from the correct distributor
    distributor_id = "550e8400-e29b-41d4-a716-446655440000"
    customer_id = "d0ad369e-8d92-4b1b-80ed-2fda2bab9be0"  # From the message
    
    try:
        # Get all orders for this distributor
        all_orders = await db.execute_query(
            table='orders',
            operation='select',
            filters={},
            distributor_id=distributor_id
        )
        
        print(f"📋 TOTAL ORDERS for distributor {distributor_id}: {len(all_orders) if all_orders else 0}")
        
        if all_orders:
            # Sort by created_at descending
            all_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            print("\n🕒 RECENT ORDERS (last 10):")
            for i, order in enumerate(all_orders[:10], 1):
                created_at = order.get('created_at', 'N/A')
                order_id = order.get('id', 'N/A')[:8] + '...'
                customer = order.get('customer_id', 'N/A')[:8] + '...'
                status = order.get('status', 'N/A')
                total = order.get('total_amount', 'N/A')
                ai_confidence = order.get('ai_confidence', 'N/A')
                
                print(f"   {i}. Order {order_id} | Customer: {customer} | Status: {status}")
                print(f"      Created: {created_at} | Total: ${total} | AI Confidence: {ai_confidence}")
        
        # Check specifically for orders from our test customer
        customer_orders = await db.execute_query(
            table='orders',
            operation='select',
            filters={'customer_id': customer_id},
            distributor_id=distributor_id
        )
        
        print(f"\n👤 ORDERS for test customer {customer_id[:8]}...: {len(customer_orders) if customer_orders else 0}")
        
        if customer_orders:
            for order in customer_orders:
                print(f"   - Order ID: {order.get('id')}")
                print(f"     Status: {order.get('status')} | Created: {order.get('created_at')}")
                print(f"     AI Message ID: {order.get('ai_source_message_id')}")
                print(f"     Total: ${order.get('total_amount')} | Confidence: {order.get('ai_confidence')}")
        
        # Check order_products for any recent orders (no distributor_id filtering)
        all_order_products = await db.execute_query(
            table='order_products',
            operation='select',
            filters={},
            distributor_id=None  # order_products table doesn't have distributor_id
        )
        
        print(f"\n📦 TOTAL ORDER PRODUCTS for distributor: {len(all_order_products) if all_order_products else 0}")
        
        if all_order_products:
            # Sort by created_at descending
            all_order_products.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            print("\n🛒 RECENT ORDER PRODUCTS (last 5):")
            for i, op in enumerate(all_order_products[:5], 1):
                order_id = op.get('order_id', 'N/A')[:8] + '...'
                product_name = op.get('product_name', 'N/A')
                quantity = op.get('quantity', 'N/A')
                ai_confidence = op.get('ai_confidence', 'N/A')
                created_at = op.get('created_at', 'N/A')
                
                print(f"   {i}. {product_name} x{quantity} | Order: {order_id}")
                print(f"      AI Confidence: {ai_confidence} | Created: {created_at}")
        
        return len(all_orders) if all_orders else 0
    
    except Exception as e:
        print(f"❌ Error checking orders: {e}")
        return 0

async def main():
    """Run the order check."""
    print("🚀 Order Creation Verification")
    print("Checking if orders are being created from confirmed products...")
    print()
    
    order_count = await check_recent_orders()
    
    print("\n" + "=" * 50)
    
    if order_count > 0:
        print("✅ Orders found in database!")
        print("The system appears to be creating orders from confirmed products.")
    else:
        print("❌ No orders found in database.")
        print("Orders may not be getting created, or there's an issue with the workflow.")

if __name__ == "__main__":
    asyncio.run(main())