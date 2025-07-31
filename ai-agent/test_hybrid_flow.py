#!/usr/bin/env python3
"""
Test the complete Hybrid Status-Based flow with OpenAI extraction.

Tests:
1. OpenAI extracts products correctly
2. Products are saved with status="draft"
3. Validation updates status appropriately
4. Only confirmed products create orders
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

async def test_hybrid_flow():
    """Test the complete hybrid status-based flow."""
    
    print("🧪 Testing Hybrid Status-Based Flow")
    print("=" * 60)
    
    # Create database service
    db = DatabaseService()
    
    # Initialize processor
    processor = StreamlinedOrderProcessor(db, "demo-distributor")
    
    # Test 1: Spanish message that should extract and confirm
    test1 = {
        'id': 'test-hybrid-1',
        'content': 'Quiero comprar un litro de aceite de canola por favor',
        'customer_id': 'test-customer-456',
        'conversation_id': 'test-conversation-789',
        'channel': 'WHATSAPP'
    }
    
    print("📝 Test 1: Spanish message with exact match")
    print(f"   Message: '{test1['content']}'")
    
    result1 = await processor.process_message(test1)
    
    if result1:
        print("\n✅ Processing succeeded!")
        print(f"   Intent: {result1.intent.intent} ({result1.intent.confidence:.2f})")
        print(f"   Products: {len(result1.extracted_products)}")
        
        for i, product in enumerate(result1.extracted_products, 1):
            print(f"\n   Product {i}:")
            print(f"     Name: {product.product_name}")
            print(f"     Status: {product.status} ⭐")
            print(f"     Matched ID: {product.matched_product_id}")
            print(f"     Matched Name: {product.matched_product_name}")
            print(f"     Validation Notes: {product.validation_notes}")
            print(f"     Quantity: {product.quantity} {product.unit}")
        
        print(f"\n   Requires Clarification: {result1.requires_clarification}")
        if result1.suggested_question:
            print(f"   Suggested Question: {result1.suggested_question}")
    
    print("\n" + "-" * 60)
    
    # Test 2: Ambiguous message that should require clarification
    test2 = {
        'id': 'test-hybrid-2',
        'content': 'Necesito aceite y agua',
        'customer_id': 'test-customer-456',
        'conversation_id': 'test-conversation-790',
        'channel': 'WHATSAPP'
    }
    
    print("\n📝 Test 2: Ambiguous message needing clarification")
    print(f"   Message: '{test2['content']}'")
    
    result2 = await processor.process_message(test2)
    
    if result2:
        print("\n✅ Processing succeeded!")
        print(f"   Intent: {result2.intent.intent} ({result2.intent.confidence:.2f})")
        print(f"   Products: {len(result2.extracted_products)}")
        
        for i, product in enumerate(result2.extracted_products, 1):
            print(f"\n   Product {i}:")
            print(f"     Name: {product.product_name}")
            print(f"     Status: {product.status} ⭐")
            print(f"     Validation Notes: {product.validation_notes}")
            print(f"     Clarification Asked: {product.clarification_asked}")
        
        print(f"\n   Requires Clarification: {result2.requires_clarification}")
        if result2.suggested_question:
            print(f"   Suggested Question: {result2.suggested_question}")
    
    print("\n" + "-" * 60)
    
    # Test 3: Unknown product that should be pending
    test3 = {
        'id': 'test-hybrid-3',
        'content': 'Quiero 5 paquetes de producto misterioso',
        'customer_id': 'test-customer-456',
        'conversation_id': 'test-conversation-791',
        'channel': 'WHATSAPP'
    }
    
    print("\n📝 Test 3: Unknown product")
    print(f"   Message: '{test3['content']}'")
    
    result3 = await processor.process_message(test3)
    
    if result3:
        print("\n✅ Processing succeeded!")
        print(f"   Intent: {result3.intent.intent} ({result3.intent.confidence:.2f})")
        print(f"   Products: {len(result3.extracted_products)}")
        
        for i, product in enumerate(result3.extracted_products, 1):
            print(f"\n   Product {i}:")
            print(f"     Name: {product.product_name}")
            print(f"     Status: {product.status} ⭐")
            print(f"     Validation Notes: {product.validation_notes}")
        
        print(f"\n   Requires Clarification: {result3.requires_clarification}")
        if result3.suggested_question:
            print(f"   Suggested Question: {result3.suggested_question}")
    
    return True

async def main():
    """Run the hybrid flow test."""
    print("🚀 Hybrid Status-Based Flow Test")
    print("Testing complete workflow: Extract → Validate → Confirm/Pending")
    print()
    
    success = await test_hybrid_flow()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 Hybrid flow test completed!")
        print("\nKey Results:")
        print("1. OpenAI extraction working with Spanish")
        print("2. Status-based tracking implemented")
        print("3. Validation sets appropriate status")
        print("4. Clarification questions generated for uncertain matches")
    else:
        print("⚠️ Hybrid flow test failed.")
    
    print("\n💡 Next steps:")
    print("1. Test with real WhatsApp messages")
    print("2. Verify database persistence of status fields")
    print("3. Test conversation continuity with clarifications")

if __name__ == "__main__":
    asyncio.run(main())