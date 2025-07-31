#!/usr/bin/env python3
"""
Direct test of order_products insertion to capture error response.
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

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def test_direct_order_products_insert():
    """Test direct insertion into order_products to see the exact error."""
    
    print("🧪 TESTING DIRECT ORDER_PRODUCTS INSERTION")
    print("=" * 60)
    
    db = DatabaseService()
    
    # Use an existing order ID (create one first if needed)
    order_id = "00000000-0000-0000-0000-000000000001"  # Dummy order ID for testing
    
    # Create the exact data structure we're trying to insert with proper defaults
    order_product_data = {
        'order_id': order_id,
        'product_name': 'aceite de canola',
        'quantity': 2,
        'product_unit': 'litros',
        'unit_price': 0.00,  # Use default value instead of None
        'line_price': 0.00,  # Use default value instead of None
        'ai_extracted': True,
        'ai_confidence': 0.85,
        'ai_original_text': '2 litros de aceite de canola',
        'matched_product_id': '229578f5-8d68-4cae-9e4c-4e96f82f2e3e',
        'matching_confidence': 0.9,
        'line_order': 1
    }
    
    print("📋 Order Product Data:")
    for key, value in order_product_data.items():
        print(f"   {key}: {value} ({type(value).__name__})")
    print()
    
    try:
        print("🚀 Attempting direct insertion...")
        
        # Try to insert directly
        result = await db.execute_query(
            table='order_products',
            operation='insert',
            data=order_product_data,
            distributor_id=None  # order_products table doesn't have distributor_id column
        )
        
        if result:
            print(f"✅ Successfully inserted order product: {result}")
        else:
            print("❌ No result returned from insertion")
        
        return True
        
    except Exception as e:
        print(f"💥 Exception during insertion: {e}")
        
        # The enhanced error logging should capture the response details
        return False

async def main():
    """Run the direct order products insertion test."""
    print("🚀 Direct Order Products Insertion Test")
    print("Testing direct insertion to capture Supabase error response...")
    print()
    
    success = await test_direct_order_products_insert()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎯 Test completed successfully!")
    else:
        print("⚠️ Test failed - check error details above")

if __name__ == "__main__":
    asyncio.run(main())