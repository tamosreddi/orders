#!/usr/bin/env python3
"""
Test real temporal continuation with server running.
Tests the actual end-to-end flow with real messages.
"""

import requests
import uuid
import time
import json
from datetime import datetime

# Configuration
AI_AGENT_URL = "http://localhost:8001"
DISTRIBUTOR_ID = "550e8400-e29b-41d4-a716-446655440000"

def create_test_message_id():
    """Create a test message ID that won't cause FK issues."""
    # Use proper UUID format for database compatibility
    return str(uuid.uuid4())

def send_message(content: str, customer_id: str, conversation_id: str) -> dict:
    """Send a message and return the response."""
    # Create a unique message ID for testing
    message_id = create_test_message_id()
    
    payload = {
        "message_id": message_id,
        "customer_id": customer_id,
        "conversation_id": conversation_id,
        "content": content,
        "distributor_id": DISTRIBUTOR_ID,
        "channel": "WHATSAPP"
    }
    
    print(f"📨 '{content}' (test-id: {message_id[:12]}...)")
    
    try:
        response = requests.post(
            f"{AI_AGENT_URL}/process-message",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            order_id = result.get('order_id')
            order_created = result.get('order_created')
            continuation_order_id = result.get('continuation_order_id')
            print(f"   ✅ order_id={order_id}, created={order_created}, continuation={continuation_order_id}")
            return result
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail.get('error_message', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return {"success": False}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {"success": False}

def main():
    """Test temporal continuation scenario."""
    print("🧪 REAL TEMPORAL CONTINUATION TEST")
    print("Scenario: 'Quiero 43 panes' → '2 pepsis'")
    print("=" * 50)
    
    # Use existing customer and conversation from database (avoid FK issues)
    customer_id = "b77b2648-529a-4a28-b83e-1923fcad6246"  # Real customer ID from DB
    conversation_id = "3c493d64-631a-4108-9f20-7739a8e34081"  # Real conversation ID from DB
    
    # Step 1: Send first message to create order
    print("\n1️⃣ Initial order:")
    result1 = send_message("Quiero 43 panes", customer_id, conversation_id)
    
    if not result1.get('success', False):
        print("❌ First message failed - cannot test continuation")
        return
    
    order1_id = result1.get('order_id')
    order1_created = result1.get('order_created')
    
    # Wait a moment to ensure temporal ordering
    time.sleep(1)
    
    # Step 2: Send second message that should continue the order
    print("\n2️⃣ Continuation message:")
    result2 = send_message("2 pepsis", customer_id, conversation_id)
    
    if not result2.get('success', False):
        print("❌ Second message failed")
        return
        
    order2_id = result2.get('order_id')
    order2_created = result2.get('order_created')
    continuation_order_id = result2.get('continuation_order_id')
    
    # Step 3: Analyze results
    print("\n" + "=" * 50)
    print("📊 ANALYSIS")
    print("=" * 50)
    
    print(f"First message ('Quiero 43 panes'):")
    print(f"   order_id: {order1_id}")
    print(f"   order_created: {order1_created}")
    
    print(f"\nSecond message ('2 pepsis'):")
    print(f"   order_id: {order2_id}")  
    print(f"   order_created: {order2_created}")
    print(f"   continuation_order_id: {continuation_order_id}")
    
    # Check success conditions
    if order1_id and continuation_order_id and order1_id == continuation_order_id:
        print(f"\n✅ SUCCESS: Temporal continuation worked!")
        print(f"   First message created order: {order1_id}")
        print(f"   Second message continued order: {continuation_order_id}")
        print(f"   'Quiero 43 panes' + '2 pepsis' = SAME ORDER ✓")
    elif order1_id and order2_id and order1_id == order2_id:
        print(f"\n✅ SUCCESS: Same order returned (continuation)")
        print(f"   Both messages used order: {order1_id}")
        print(f"   'Quiero 43 panes' + '2 pepsis' = SAME ORDER ✓")
    elif order1_id and order2_id and order1_id != order2_id:
        print(f"\n❌ FAILED: Different orders created")
        print(f"   Order 1: {order1_id}")
        print(f"   Order 2: {order2_id}")
        print(f"   Continuation: {continuation_order_id}")
        print(f"   Expected: SAME order for both messages")
        
        # Additional debugging
        print(f"\n🔍 DEBUG INFO:")
        print(f"   Message 1 result: {json.dumps(result1, indent=2)}")
        print(f"   Message 2 result: {json.dumps(result2, indent=2)}")
    else:
        print(f"\n❌ FAILED: Missing order information")
        print(f"   Order 1: {order1_id}")
        print(f"   Order 2: {order2_id}")
        print(f"   Continuation: {continuation_order_id}")

if __name__ == "__main__":
    main()