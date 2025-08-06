#!/usr/bin/env python3
"""
Quick test script for the streamlined Order Agent system.

Tests basic functionality without complex dependencies.
"""

import asyncio
import json
from typing import Dict, Any

# Mock message data for testing
SAMPLE_MESSAGES = [
    {
        'id': 'msg001',
        'content': 'Quiero 5 botellas de agua',
        'customer_id': 'cust001',
        'conversation_id': 'conv001',
        'channel': 'WHATSAPP'
    },
    {
        'id': 'msg002', 
        'content': 'Cuanto cuesta la leche?',
        'customer_id': 'cust002',
        'conversation_id': 'conv002',
        'channel': 'WHATSAPP'
    },
    {
        'id': 'msg003',
        'content': 'Mi pedido llegó mal',
        'customer_id': 'cust003',
        'conversation_id': 'conv003', 
        'channel': 'WHATSAPP'
    }
]


async def test_message_analysis():
    """Test message analysis without database."""
    from agents.order_agent import StreamlinedOrderProcessor
    from services.database import DatabaseService
    
    print("🧪 Testing Streamlined Order Agent...")
    
    # Create mock database service (won't actually connect)
    database = DatabaseService()
    distributor_id = "test-distributor"
    
    # Create processor
    processor = StreamlinedOrderProcessor(database, distributor_id)
    
    # Test intent parsing without OpenAI calls
    print("\n📝 Testing intent parsing...")
    
    test_cases = [
        ("Quiero 5 botellas de agua", "BUY"),
        ("Cuanto cuesta la leche?", "QUESTION"),
        ("Mi pedido llegó mal", "COMPLAINT"),
        ("Hola como estas", "OTHER")
    ]
    
    for content, expected_intent in test_cases:
        # Test the parsing logic directly
        intent = processor._parse_intent("", content)
        print(f"  '{content[:30]}...' → {intent.intent} (expected: {expected_intent})")
        
        if intent.intent == expected_intent:
            print("    ✅ PASS")
        else:
            print("    ❌ FAIL")
    
    print("\n🛍️ Testing product extraction...")
    
    product_test_cases = [
        "Quiero 5 botellas de agua",
        "Necesito 3 cajas de cerveza y 2 leche",
        "10 coca cola por favor"
    ]
    
    for content in product_test_cases:
        products = processor._parse_products("", content)
        print(f"  '{content}' → {len(products)} products")
        for product in products:
            print(f"    - {product.quantity}x {product.product_name}")
    
    print("\n✅ Basic functionality test complete!")
    print("\n🔧 To test full system:")
    print("  1. Start: python main.py")
    print("  2. Test API: curl http://localhost:8001/health")
    print("  3. Send sample message to webhook")


async def test_api_syntax():
    """Test that API imports work correctly."""
    try:
        from api import app, MessageProcessingRequest, MessageProcessingResponse
        print("✅ API imports successful")
        
        # Test creating request model
        request = MessageProcessingRequest(
            message_id="test",
            customer_id="test", 
            conversation_id="test",
            content="test message",
            distributor_id=None
        )
        print("✅ Request model creation successful")
        
    except Exception as e:
        print(f"❌ API import failed: {e}")


async def test_main_syntax():
    """Test that main imports work correctly."""
    try:
        from main import OrderAgentMain
        print("✅ Main imports successful")
        
        # Test creating main class
        app = OrderAgentMain()
        print("✅ Main class creation successful")
        
    except Exception as e:
        print(f"❌ Main import failed: {e}")


if __name__ == "__main__":
    print("🚀 Testing Streamlined Order Agent System")
    print("=" * 50)
    
    asyncio.run(test_api_syntax())
    print()
    asyncio.run(test_main_syntax()) 
    print()
    asyncio.run(test_message_analysis())