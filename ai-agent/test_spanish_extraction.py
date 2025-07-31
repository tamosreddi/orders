#!/usr/bin/env python3
"""
Test script for enhanced Spanish product extraction.

Tests the user's specific message: "Quiero comprar un litro de aceite de canola por favor"
Expected extraction:
- Product: "aceite de canola"
- Quantity: 1 (from "un")
- Unit: "litro"
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.order_agent import StreamlinedOrderProcessor
from services.database import DatabaseService
from schemas.message import MessageIntent

def test_spanish_extraction():
    """Test the enhanced Spanish product extraction directly."""
    
    # Create a mock processor just to test the _parse_products method
    mock_db = None  # We won't use the database for this test
    processor = StreamlinedOrderProcessor(mock_db, "test-distributor")
    
    # Test message from the user
    test_message = "Quiero comprar un litro de aceite de canola por favor"
    mock_response = ""  # We're testing _parse_products directly, not OpenAI response
    
    print(f"🧪 Testing Spanish extraction for: '{test_message}'")
    print("=" * 60)
    
    # Call the enhanced _parse_products method
    extracted_products = processor._parse_products(mock_response, test_message)
    
    print(f"📊 Extraction Results:")
    print(f"   Number of products found: {len(extracted_products)}")
    print()
    
    if extracted_products:
        for i, product in enumerate(extracted_products, 1):
            print(f"   Product {i}:")
            print(f"     Name: {product.product_name}")
            print(f"     Quantity: {product.quantity}")
            print(f"     Unit: {product.unit}")
            print(f"     Confidence: {product.confidence}")
            print(f"     Original text: {product.original_text}")
            print()
        
        # Verify expected results
        expected_product = extracted_products[0]
        success = True
        
        if expected_product.product_name != "aceite de canola":
            print(f"❌ FAIL: Expected product 'aceite de canola', got '{expected_product.product_name}'")
            success = False
        
        if expected_product.quantity != 1:
            print(f"❌ FAIL: Expected quantity 1, got {expected_product.quantity}")
            success = False
        
        if expected_product.unit != "litro":
            print(f"❌ FAIL: Expected unit 'litro', got '{expected_product.unit}'")
            success = False
        
        if success:
            print("✅ SUCCESS: All expected values extracted correctly!")
            print("   ✓ Product: aceite de canola")
            print("   ✓ Quantity: 1 (from 'un')")
            print("   ✓ Unit: litro")
        
    else:
        print("❌ FAIL: No products extracted from the message!")
        print("This indicates the Spanish extraction is not working properly.")
    
    print("\n" + "=" * 60)
    print("🔍 Detailed Analysis:")
    
    # Test the individual components
    print("\n1. Testing Spanish number recognition:")
    spanish_numbers = {
        'un': 1, 'una': 1, 'uno': 1,
        'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5
    }
    test_words = test_message.lower().split()
    found_numbers = [word for word in test_words if word in spanish_numbers]
    print(f"   Found Spanish numbers: {found_numbers}")
    if found_numbers:
        print(f"   'un' → {spanish_numbers.get('un', 'NOT FOUND')}")
    
    print("\n2. Testing product keyword matching:")
    product_keywords = {
        'aceite de canola': 'aceite de canola',
        'aceite canola': 'aceite de canola',
        'aceite': 'aceite'
    }
    found_keywords = [keyword for keyword in product_keywords.keys() if keyword in test_message.lower()]
    print(f"   Found product keywords: {found_keywords}")
    
    print("\n3. Testing unit recognition:")
    spanish_units = {
        'litro': 'litro', 'litros': 'litro',
        'botella': 'botella', 'botellas': 'botella'
    }
    found_units = [word for word in test_words if word in spanish_units]
    print(f"   Found units: {found_units}")
    
    return len(extracted_products) > 0

if __name__ == "__main__":
    print("🚀 Starting Spanish Product Extraction Test")
    print("Testing user message: 'Quiero comprar un litro de aceite de canola por favor'")
    print()
    
    success = test_spanish_extraction()
    
    if success:
        print("\n🎉 Test completed successfully! The enhanced Spanish extraction is working.")
    else:
        print("\n⚠️ Test failed. The Spanish extraction needs debugging.")
    
    print("\n💡 Next steps:")
    print("1. If successful: Test with the actual AI agent API")
    print("2. If failed: Debug the _parse_products method implementation")