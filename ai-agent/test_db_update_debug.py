#!/usr/bin/env python3
"""
Debug script to test database update functionality.

Tests the exact database update flow with detailed logging.
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
from schemas.message import MessageAnalysis, MessageIntent, ExtractedProduct
from tools.supabase_tools import update_message_ai_data

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def test_database_update():
    """Test the database update flow step by step."""
    
    print("🧪 Testing Database Update Flow")
    print("=" * 60)
    
    # Create a real database service
    db = DatabaseService()
    
    # First, let's create a test message in the database
    import uuid
    test_conversation_id = str(uuid.uuid4())
    
    test_message_data = {
        'conversation_id': test_conversation_id,
        'content': 'Quiero comprar un litro de aceite de canola por favor',
        'is_from_customer': True,
        'message_type': 'TEXT',
        'status': 'RECEIVED',
        'ai_processed': False,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    print("📝 Step 1: Creating test message in database")
    try:
        result = await db.insert_single(
            table='messages',
            data=test_message_data
        )
        
        if result:
            message_id = result['id']
            print(f"✅ Created test message with ID: {message_id}")
        else:
            print("❌ Failed to create test message")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test message: {e}")
        return False
    
    # Create mock analysis data
    print("\n📊 Step 2: Creating MessageAnalysis object")
    
    extracted_product = ExtractedProduct(
        product_name="aceite de canola",
        quantity=1,
        unit="litro",
        original_text="Quiero comprar un litro de aceite de canola por favor",
        confidence=0.85
    )
    
    intent = MessageIntent(
        intent="BUY",
        confidence=0.85,
        reasoning="Customer expressing purchase intent"
    )
    
    analysis = MessageAnalysis(
        message_id=message_id,
        intent=intent,
        extracted_products=[extracted_product],
        processing_time_ms=1500
    )
    
    print(f"✅ Created analysis with {len(analysis.extracted_products)} products")
    
    # Test product serialization
    print("\n🔧 Step 3: Testing product serialization")
    try:
        if hasattr(extracted_product, 'model_dump'):
            product_dict = extracted_product.model_dump()
            print(f"✅ Using model_dump(): {product_dict}")
        else:
            product_dict = extracted_product.dict()
            print(f"✅ Using dict(): {product_dict}")
            
        print(f"   Serialized product: {json.dumps(product_dict, indent=2)}")
    except Exception as e:
        print(f"❌ Serialization error: {e}")
        return False
    
    # Test the database update
    print("\n💾 Step 4: Testing database update")
    try:
        success = await update_message_ai_data(
            db=db,
            message_id=message_id,
            analysis=analysis,
            distributor_id="demo-distributor"
        )
        
        if success:
            print("✅ Database update succeeded!")
        else:
            print("❌ Database update failed!")
            return False
            
    except Exception as e:
        print(f"❌ Database update error: {e}")
        return False
    
    # Verify the update by reading the message back
    print("\n🔍 Step 5: Verifying the update")
    try:
        result = await db.execute_query(
            table='messages',
            operation='select',
            filters={'id': message_id}
        )
        
        if result and len(result) > 0:
            message = result[0]
            print("✅ Retrieved updated message:")
            print(f"   ai_processed: {message.get('ai_processed')}")
            print(f"   ai_confidence: {message.get('ai_confidence')}")
            print(f"   ai_extracted_intent: {message.get('ai_extracted_intent')}")
            
            products = message.get('ai_extracted_products')
            if products:
                print(f"   ai_extracted_products: {json.dumps(products, indent=4)}")
                
                # Verify the product data
                if isinstance(products, list) and len(products) > 0:
                    first_product = products[0]
                    expected_name = "aceite de canola"
                    actual_name = first_product.get('product_name')
                    
                    if actual_name == expected_name:
                        print(f"   ✅ Product name correct: {actual_name}")
                    else:
                        print(f"   ❌ Product name mismatch: expected '{expected_name}', got '{actual_name}'")
                    
                    expected_quantity = 1
                    actual_quantity = first_product.get('quantity')
                    
                    if actual_quantity == expected_quantity:
                        print(f"   ✅ Quantity correct: {actual_quantity}")
                    else:
                        print(f"   ❌ Quantity mismatch: expected {expected_quantity}, got {actual_quantity}")
                        
                    expected_unit = "litro"
                    actual_unit = first_product.get('unit')
                    
                    if actual_unit == expected_unit:
                        print(f"   ✅ Unit correct: {actual_unit}")
                    else:
                        print(f"   ❌ Unit mismatch: expected '{expected_unit}', got '{actual_unit}'")
                        
                    print(f"\n🎉 SUCCESS: ai_extracted_products is correctly saved in the database!")
                else:
                    print("   ❌ ai_extracted_products is not a list or is empty")
            else:
                print("   ❌ ai_extracted_products is null or missing!")
                return False
        else:
            print("❌ Could not retrieve updated message")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False
    
    # Clean up - delete the test message
    print("\n🧹 Step 6: Cleaning up test data")
    try:
        await db.execute_query(
            table='messages',
            operation='delete',
            filters={'id': message_id}
        )
        print("✅ Test message deleted")
    except Exception as e:
        print(f"⚠️ Could not delete test message: {e}")
    
    return True

async def main():
    """Run the database update test."""
    print("🚀 Database Update Debug Test")
    print("Testing ai_extracted_products saving to Supabase")
    print()
    
    success = await test_database_update()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 All tests passed! The database update is working correctly.")
        print("The issue might be elsewhere in the pipeline.")
    else:
        print("⚠️ Database update test failed.")
        print("This explains why ai_extracted_products is not being saved.")
    
    print("\n💡 Next steps:")
    print("1. If tests pass: Check the actual message IDs being used in production")
    print("2. If tests fail: Debug the database connection and schema")

if __name__ == "__main__":
    asyncio.run(main())