"""
Test temporal continuation for the exact scenario:
1. "Quiero 43 panes" -> creates order
2. "2 pepsis" -> should add to same order
"""

import time
import requests
import uuid

AI_AGENT_URL = "http://localhost:8001"
DISTRIBUTOR_ID = "550e8400-e29b-41d4-a716-446655440000"

def send_message(content: str, customer_id: str, conversation_id: str) -> dict:
    """Send a message and return the response."""
    message_id = str(uuid.uuid4())
    
    payload = {
        "message_id": message_id,
        "customer_id": customer_id,
        "conversation_id": conversation_id,
        "content": content,
        "distributor_id": DISTRIBUTOR_ID,
        "channel": "WHATSAPP"
    }
    
    print(f"📨 '{content}' (message_id: {message_id[:8]}...)")
    
    try:
        response = requests.post(
            f"{AI_AGENT_URL}/process-message",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45
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
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response text: {response.text[:200]}")
            return {"success": False}
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False}

def main():
    """Test temporal continuation scenario."""
    print("🧪 TEMPORAL CONTINUATION TEST")
    print("Scenario: 'Quiero 43 panes' → '2 pepsis'")
    print("=" * 50)
    
    # Use existing customer/conversation
    customer_id = "d0ad369e-8d92-4b1b-80ed-2fda2bab9be0"
    conversation_id = "56d78925-2a57-4ff8-93dd-27e5557d0d8c"
    
    # Message 1: Create initial order
    print("\\n1️⃣ Initial order:")
    result1 = send_message("Quiero 43 panes", customer_id, conversation_id)
    order1_id = result1.get('order_id') if result1 else None
    
    if not order1_id:
        print("❌ First message failed - cannot test continuation")
        return
    
    # Small delay to simulate real usage
    print("\\n⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    # Message 2: Should continue to same order
    print("\\n2️⃣ Continuation message:")
    result2 = send_message("2 pepsis", customer_id, conversation_id)
    order2_id = result2.get('order_id') if result2 else None
    
    # Analysis
    print("\\n" + "=" * 50)
    print("📊 ANALYSIS")
    print("=" * 50)
    
    # Check for continuation order ID in second message
    continuation_order_id = result2.get('continuation_order_id') if result2 else None
    
    if order1_id and continuation_order_id and order1_id == continuation_order_id:
        print("✅ SUCCESS: Temporal continuation worked!")
        print(f"   First message created order: {order1_id}")
        print(f"   Second message continued order: {continuation_order_id}")
        print("   'Quiero 43 panes' + '2 pepsis' = SAME ORDER")
    elif order1_id and order2_id and order1_id == order2_id:
        print("✅ SUCCESS: Same order returned (continuation)")
        print(f"   Both messages used order: {order1_id}")
        print("   'Quiero 43 panes' + '2 pepsis' = SAME ORDER")
    elif order1_id and order2_id and order1_id != order2_id:
        print("❌ FAILED: Different orders created")
        print(f"   Order 1: {order1_id}")
        print(f"   Order 2: {order2_id}")
        print(f"   Continuation: {continuation_order_id}")
        print("   Expected: SAME order for both messages")
    else:
        print("❌ FAILED: Missing order information")
        print(f"   Order 1: {order1_id}")
        print(f"   Order 2: {order2_id}")
        print(f"   Continuation: {continuation_order_id}")

if __name__ == "__main__":
    main()