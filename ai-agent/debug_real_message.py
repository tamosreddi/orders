#!/usr/bin/env python3
"""
Debug why real WhatsApp messages don't trigger order creation.

Test using the actual message data from your recent WhatsApp test.
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
from agents.order_agent import StreamlinedOrderProcessor
from config.settings import settings

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def debug_real_message():
    """Debug the real WhatsApp message processing logic."""
    
    print("🔍 DEBUGGING REAL WHATSAPP MESSAGE PROCESSING")
    print("=" * 60)
    
    # Create database service
    db = DatabaseService()
    
    # Use the correct distributor UUID for real WhatsApp messages
    distributor_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Initialize processor
    processor = StreamlinedOrderProcessor(db, distributor_id)
    
    # Get the real message data from database
    message_query = """
    SELECT 
        id, content, conversation_id,
        ai_extracted_products
    FROM messages 
    WHERE id = 'cf6e8df5-e3d8-4b58-8268-bb8cfefec18d'
    """
    
    messages = await db.execute_query(
        table='messages',
        operation='select',
        filters={'id': 'cf6e8df5-e3d8-4b58-8268-bb8cfefec18d'}
    )
    
    if not messages or len(messages) == 0:
        print("❌ Message not found in database")
        return False
    
    message_result = messages[0]
    
    # Get conversation to find customer_id
    conversations = await db.execute_query(
        table='conversations',
        operation='select',
        filters={'id': message_result['conversation_id']}
    )
    
    if not conversations or len(conversations) == 0:
        print("❌ Conversation not found")
        return False
    
    conv_result = conversations[0]
    
    # Simulate the exact message data structure the API would have
    message_data = {
        'id': message_result['id'],
        'content': message_result['content'],
        'customer_id': conv_result['customer_id'],
        'conversation_id': message_result['conversation_id'],
        'channel': 'WHATSAPP'
    }
    
    print("📋 Real Message Data:")
    print(f"   Message ID: {message_data['id']}")
    print(f"   Content: '{message_data['content']}'")
    print(f"   Customer ID: {message_data['customer_id']}")
    print(f"   Existing Products: {message_result['ai_extracted_products']}")
    print()
    
    print("🔧 DEBUG SETTINGS:")
    print(f"   AI Confidence Threshold: {settings.ai_confidence_threshold}")
    print(f"   OpenAI Model: {settings.openai_model}")
    print()
    
    # Process the message and capture detailed debug info
    print("⚡ PROCESSING MESSAGE (with debug logging)...")
    print("-" * 40)
    
    try:
        # This will show us exactly what happens in the real flow
        analysis = await processor.process_message(message_data)
        
        if analysis:
            print("\n🔍 ANALYSIS RESULTS:")
            print(f"   Intent: {analysis.intent.intent}")
            print(f"   Intent Confidence: {analysis.intent.confidence}")
            print(f"   Products Count: {len(analysis.extracted_products)}")
            print(f"   Requires Clarification: {analysis.requires_clarification}")
            print(f"   Suggested Question: {analysis.suggested_question}")
            
            print("\n📦 PRODUCTS DETAIL:")
            for i, product in enumerate(analysis.extracted_products, 1):
                print(f"   Product {i}:")
                print(f"     Name: {product.product_name}")
                print(f"     Status: {product.status} ⭐")
                print(f"     Confidence: {product.confidence}")
                print(f"     Matched ID: {product.matched_product_id}")
            
            # Check the specific conditions for order creation
            print("\n🎯 ORDER CREATION CONDITIONS:")
            print(f"   1. BUY Intent: {analysis.intent.intent == 'BUY'}")
            print(f"   2. Has Products: {bool(analysis.extracted_products)}")
            print(f"   3. Confidence >= Threshold: {analysis.intent.confidence} >= {settings.ai_confidence_threshold} = {analysis.intent.confidence >= settings.ai_confidence_threshold}")
            print(f"   4. NOT Requires Clarification: not {analysis.requires_clarification} = {not analysis.requires_clarification}")
            
            should_create_order = (
                analysis.intent.intent == "BUY" and
                analysis.extracted_products and 
                analysis.intent.confidence >= settings.ai_confidence_threshold and
                not analysis.requires_clarification
            )
            
            print(f"\n   🚀 SHOULD CREATE ORDER: {should_create_order}")
            
            if not should_create_order:
                print("\n❌ ORDER NOT CREATED - Failed conditions above")
            else:
                print("\n✅ All conditions met - order should be created")
        
        else:
            print("\n❌ Message processing returned None")
        
        return analysis is not None
        
    except Exception as e:
        print(f"\n💥 EXCEPTION during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the real message debugging."""
    print("🚀 Real WhatsApp Message Debug Session")
    print("Debugging your actual message: 'Hola quiero 2 litros de aceite de canola'")
    print()
    
    success = await debug_real_message()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎯 Debug completed!")
        print("\nThis will show exactly why order creation isn't happening.")
    else:
        print("⚠️ Debug failed.")

if __name__ == "__main__":
    asyncio.run(main())