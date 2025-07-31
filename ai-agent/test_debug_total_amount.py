#!/usr/bin/env python3
"""
Debug total_amount issue specifically
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from decimal import Decimal

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.database import DatabaseService
from agents.order_agent import StreamlinedOrderProcessor
from schemas.message import MessageAnalysis, MessageIntent, ExtractedProduct

# Set up DEBUG logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def debug_total_amount():
    """Debug the total_amount issue."""
    
    print("🔍 DEBUGGING TOTAL_AMOUNT ISSUE")
    print("=" * 60)
    
    # Create database service
    db = DatabaseService()
    
    # Use proper distributor UUID
    distributor_id = "69f73909-7190-4c39-b2d6-8c8066c8bea1"
    
    # Initialize processor with proper UUID
    processor = StreamlinedOrderProcessor(db, distributor_id)
    
    # Use REAL UUIDs from the successful message
    real_message_id = "983aa8d2-1ac5-450f-bc70-3e6901fabd29"
    real_conversation_id = "56d78925-2a57-4ff8-93dd-27e5557d0d8c"
    real_customer_id = "d0ad369e-8d92-4b1b-80ed-2fda2bab9be0"
    
    # Create the confirmed product with explicit unit_price
    confirmed_product = ExtractedProduct(
        product_name="aceite de canola",
        quantity=1,
        unit="litro",
        original_text="1 litro de aceite de canola",
        confidence=0.85,
        status="confirmed",
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
        message_id=real_message_id,
        intent=intent,
        extracted_products=[confirmed_product],
        processing_time_ms=1000
    )
    
    # Message data with ALL proper UUIDs
    message_data = {
        'id': real_message_id,
        'content': 'Hola quiero 1 litro de aceite de canola',
        'customer_id': real_customer_id,
        'conversation_id': real_conversation_id,
        'channel': 'WHATSAPP'
    }
    
    print("🧪 Testing with DEBUG logging enabled...")
    print()
    
    try:
        order_created = await processor._create_simple_order(message_data, analysis)
        
        if order_created:
            print("   🎉 SUCCESS! Order created!")
        else:
            print("   ❌ FAILED! Check debug logs above")
            
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    return order_created

if __name__ == "__main__":
    asyncio.run(debug_total_amount())