#!/usr/bin/env python3
"""
Test updating a real message from the user's system.

This will help us see what's happening with their actual messages.
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
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def test_with_existing_message():
    """Test updating an existing message from the user's system."""
    
    print("🧪 Testing with Existing Message")
    print("=" * 60)
    
    # Create a real database service
    db = DatabaseService()
    
    # First, let's get the most recent message from the database
    print("📝 Step 1: Finding recent messages")
    try:
        # Get recent messages (should bypass RLS for read operations)
        result = await db.execute_query(
            table='messages',
            operation='select',
            filters={'is_from_customer': True, 'ai_processed': False}
        )
        
        if result and len(result) > 0:
            # Use the most recent unprocessed message
            message = result[0]
            message_id = message['id']
            content = message['content']
            
            print(f"✅ Found message to test:")
            print(f"   ID: {message_id}")
            print(f"   Content: '{content}'")
            print(f"   Current ai_processed: {message.get('ai_processed')}")
            print(f"   Current ai_extracted_products: {message.get('ai_extracted_products')}")
        else:
            print("❌ No unprocessed customer messages found")
            return False
            
    except Exception as e:
        print(f"❌ Error finding messages: {e}")
        return False
    
    # Create mock analysis data for this message
    print("\n📊 Step 2: Creating mock analysis for this message")
    
    # Check if it's the Spanish message we're testing
    if "aceite" in content.lower() and "litro" in content.lower():
        print("✅ This looks like our Spanish test message!")
        
        extracted_product = ExtractedProduct(
            product_name="aceite de canola",
            quantity=1,
            unit="litro",
            original_text=content,
            confidence=0.85
        )
        
        intent = MessageIntent(
            intent="BUY",
            confidence=0.85,
            reasoning="Customer expressing purchase intent"
        )
        
    else:
        print(f"This is a different message: '{content[:50]}...'")
        
        # Create generic analysis
        extracted_product = ExtractedProduct(
            product_name="test product",
            quantity=1,
            unit="unit",
            original_text=content,
            confidence=0.75
        )
        
        intent = MessageIntent(
            intent="OTHER",
            confidence=0.75,
            reasoning="Test message analysis"
        )
    
    analysis = MessageAnalysis(
        message_id=message_id,
        intent=intent,
        extracted_products=[extracted_product],
        processing_time_ms=1500
    )
    
    print(f"✅ Created analysis with {len(analysis.extracted_products)} products")
    
    # Test the database update with verbose logging
    print("\n💾 Step 3: Testing database update")
    
    # Enable debug logging for this test
    logging.getLogger('tools.supabase_tools').setLevel(logging.DEBUG)
    
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
        import traceback
        traceback.print_exc()
        return False
    
    # Verify the update by reading the message back
    print("\n🔍 Step 4: Verifying the update")
    try:
        result = await db.execute_query(
            table='messages',
            operation='select',
            filters={'id': message_id}
        )
        
        if result and len(result) > 0:
            updated_message = result[0]
            print("✅ Retrieved updated message:")
            print(f"   ai_processed: {updated_message.get('ai_processed')}")
            print(f"   ai_confidence: {updated_message.get('ai_confidence')}")
            print(f"   ai_extracted_intent: {updated_message.get('ai_extracted_intent')}")
            
            products = updated_message.get('ai_extracted_products')
            if products:
                print(f"   ai_extracted_products: {json.dumps(products, indent=4)}")
                print(f"\n🎉 SUCCESS: ai_extracted_products has been saved!")
                return True
            else:
                print("   ❌ ai_extracted_products is still null!")
                return False
        else:
            print("❌ Could not retrieve updated message")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

async def main():
    """Run the real message update test."""
    print("🚀 Real Message Update Test")
    print("Testing ai_extracted_products update on existing message")
    print()
    
    success = await test_with_existing_message()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 SUCCESS: The database update is working!")
        print("The issue was just with creating test data due to RLS policies.")
    else:
        print("⚠️ Database update still not working.")
        print("This indicates a real problem with the update mechanism.")
    
    print("\n💡 Next steps:")
    print("1. If successful: The AI agent should be saving products correctly")
    print("2. If failed: Check authentication and RLS policies")

if __name__ == "__main__":
    asyncio.run(main())