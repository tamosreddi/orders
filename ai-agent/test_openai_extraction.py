#!/usr/bin/env python3
"""
Test the updated OpenAI-first extraction approach.

Tests the exact message that was failing before to verify the fix works.
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

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def test_openai_extraction():
    """Test the OpenAI-first extraction with the user's Spanish message."""
    
    print("🧪 Testing OpenAI-First Extraction")
    print("=" * 60)
    
    # Create database service
    db = DatabaseService()
    
    # Initialize processor
    processor = StreamlinedOrderProcessor(db, "demo-distributor")
    
    # Test message data
    test_message = {
        'id': 'test-openai-123',
        'content': 'Quiero comprar un litro de aceite de canola por favor',
        'customer_id': 'test-customer-456',
        'conversation_id': 'test-conversation-789',
        'channel': 'WHATSAPP'
    }
    
    print(f"📝 Testing message: '{test_message['content']}'")
    print()
    
    try:
        # Process the message
        print("🤖 Processing with OpenAI...")
        result = await processor.process_message(test_message)
        
        if result:
            print("\n✅ Processing succeeded!")
            print(f"\n📊 Analysis Results:")
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
                    print(f"     Original text: {product.original_text}")
                
                # Verify expected results
                first_product = result.extracted_products[0]
                
                print(f"\n🎯 Verification:")
                checks = []
                
                if "aceite" in first_product.product_name.lower():
                    print(f"   ✅ Product contains 'aceite': {first_product.product_name}")
                    checks.append(True)
                else:
                    print(f"   ❌ Product doesn't contain 'aceite': {first_product.product_name}")
                    checks.append(False)
                
                if first_product.quantity == 1:
                    print(f"   ✅ Quantity is 1 (from 'un')")
                    checks.append(True)
                else:
                    print(f"   ❌ Quantity is not 1: {first_product.quantity}")
                    checks.append(False)
                
                if first_product.unit == "litro":
                    print(f"   ✅ Unit is 'litro'")
                    checks.append(True)
                else:
                    print(f"   ❌ Unit is not 'litro': {first_product.unit}")
                    checks.append(False)
                
                if all(checks):
                    print(f"\n🎉 PERFECT! OpenAI extraction working correctly!")
                    
                    # Test if it would save to database
                    print(f"\n💾 Database update simulation:")
                    products_json = []
                    for p in result.extracted_products:
                        product_dict = {
                            'product_name': p.product_name,
                            'quantity': p.quantity,
                            'unit': p.unit,
                            'confidence': p.confidence,
                            'original_text': p.original_text
                        }
                        products_json.append(product_dict)
                    
                    print(f"   ai_extracted_products will contain:")
                    print(f"   {json.dumps(products_json, indent=2)}")
                    
                    return True
                else:
                    print(f"\n⚠️ Some extraction issues found")
                    return False
            else:
                print(f"\n❌ No products extracted!")
                return False
        else:
            print("❌ Processing failed - result is None")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the OpenAI extraction test."""
    print("🚀 OpenAI-First Extraction Test")
    print("Testing: 'Quiero comprar un litro de aceite de canola por favor'")
    print()
    
    success = await test_openai_extraction()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 OpenAI-first extraction is working correctly!")
        print("The Spanish message should now save properly to ai_extracted_products.")
    else:
        print("⚠️ OpenAI extraction still has issues.")
        print("Check the logs above for details.")
    
    print("\n💡 Next steps:")
    print("1. If successful: Test with the actual WhatsApp message")
    print("2. If failed: Check OpenAI API response and parsing logic")

if __name__ == "__main__":
    asyncio.run(main())