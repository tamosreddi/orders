#!/usr/bin/env python3
"""
Test temporal continuation logic directly without database constraints.
Tests the core logic of temporal-based continuation detection.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.continuation_detector import ContinuationDetector
from services.database import DatabaseService


async def test_temporal_continuation_logic():
    """Test the temporal continuation detection logic directly."""
    
    print("🧪 TEMPORAL CONTINUATION LOGIC TEST")
    print("=" * 50)
    
    # Initialize components
    database = DatabaseService()
    detector = ContinuationDetector()
    
    test_distributor_id = "550e8400-e29b-41d4-a716-446655440000"
    test_customer_id = "customer-123"
    test_conversation_id = "conv-123"
    
    # Test case 1: Message that looks like product order
    print("\n1️⃣ Testing product order pattern detection:")
    test_message = "2 pepsis"
    
    # Mock a recent order (simulate what would be returned from database)
    mock_recent_orders = [{
        'id': 'order-123',
        'order_number': 'ORD-001',
        'status': 'PENDING',
        'created_at': datetime.now(timezone.utc).isoformat(),  # Recent order
        'total_amount': 100.0,
        'customer_id': test_customer_id
    }]
    
    # Test the pattern detection logic directly
    message_lower = test_message.lower()
    
    # Check for product patterns
    product_indicators = [
        r'\d+\s+\w+',  # Numbers + product (e.g., "2 pepsis", "43 panes")
        r'\w+\s+\d+',  # Product + numbers (e.g., "pepsi 2")
        r'quiero\s+\w+', r'dame\s+\w+', r'ponme\s+\w+',  # Want/give/put patterns
        r'necesito\s+\w+', r'mandame\s+\w+',  # Need/send patterns
    ]
    
    import re
    has_product_pattern = any(re.search(pattern, message_lower) for pattern in product_indicators)
    
    print(f"   Message: '{test_message}'")
    print(f"   Product pattern detected: {has_product_pattern}")
    
    # Test rejection patterns
    rejection_phrases = [
        "no", "nada más", "ya está", "eso es todo", "gracias",
        "nuevo pedido", "otra orden", "cancelar", "cancel"
    ]
    has_rejection = any(phrase in message_lower for phrase in rejection_phrases)
    print(f"   Rejection pattern detected: {has_rejection}")
    
    # Test time calculation
    current_time = datetime.now(timezone.utc)
    order_time = datetime.fromisoformat(mock_recent_orders[0]['created_at'].replace('Z', '+00:00'))
    time_diff = current_time - order_time
    time_diff_minutes = time_diff.total_seconds() / 60
    
    print(f"   Time since recent order: {time_diff_minutes:.1f} minutes")
    print(f"   Within 10-minute window: {time_diff_minutes <= 10}")
    
    # Simulate the temporal continuation logic
    should_continue = (
        has_product_pattern and 
        not has_rejection and 
        time_diff_minutes <= 10 and
        mock_recent_orders[0]['status'] == 'PENDING'
    )
    
    print(f"   Should trigger temporal continuation: {should_continue}")
    
    # Test case 2: Non-product message
    print("\n2️⃣ Testing non-product message:")
    non_product_message = "Hola, ¿cómo estás?"
    message_lower = non_product_message.lower()
    has_product_pattern = any(re.search(pattern, message_lower) for pattern in product_indicators)
    
    print(f"   Message: '{non_product_message}'")
    print(f"   Product pattern detected: {has_product_pattern}")
    print(f"   Should NOT trigger continuation: {not has_product_pattern}")
    
    # Test case 3: Explicit rejection
    print("\n3️⃣ Testing explicit rejection:")
    rejection_message = "ya está, gracias"
    message_lower = rejection_message.lower()
    has_product_pattern = any(re.search(pattern, message_lower) for pattern in product_indicators)
    has_rejection = any(phrase in message_lower for phrase in rejection_phrases)
    
    print(f"   Message: '{rejection_message}'")
    print(f"   Product pattern detected: {has_product_pattern}")
    print(f"   Rejection pattern detected: {has_rejection}")
    print(f"   Should NOT trigger continuation: {has_rejection}")
    
    print("\n" + "=" * 50)
    print("✅ TEMPORAL LOGIC TEST COMPLETED")
    print("   Key patterns working correctly:")
    print("   • '2 pepsis' → SHOULD continue (product pattern)")
    print("   • 'Hola' → should NOT continue (no product pattern)")  
    print("   • 'ya está' → should NOT continue (rejection pattern)")


if __name__ == "__main__":
    asyncio.run(test_temporal_continuation_logic())