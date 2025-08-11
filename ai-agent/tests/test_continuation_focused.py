"""
Focused test for continuation functionality - tests the core issue quickly.
"""

import time
import requests
import uuid
from typing import Dict, Any

AI_AGENT_URL = "http://localhost:8001"
DISTRIBUTOR_ID = "550e8400-e29b-41d4-a716-446655440000"

def create_message_in_db(message_id: str, content: str, customer_id: str, conversation_id: str) -> bool:
    """Create a message in the database first."""
    import requests
    
    # Use the Supabase API to create the message
    supabase_url = "https://ckapulfmocievprlnzux.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrYXB1bGZtb2NpZXZwcmxuenV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI3MTEzNTYsImV4cCI6MjA2ODI4NzM1Nn0.S6rAjdQXBZtmOs5MCm6CDtCvx_Hg3bmYgHOKajo5adk"
    
    message_data = {
        "id": message_id,
        "conversation_id": conversation_id,
        "content": content,
        "is_from_customer": True,
        "message_type": "TEXT",
        "status": "RECEIVED",
        "ai_processed": False,
        "channel": "WHATSAPP",
        "created_at": "2025-08-06T18:00:00.000Z",
        "updated_at": "2025-08-06T18:00:00.000Z"
    }
    
    try:
        response = requests.post(
            f"{supabase_url}/rest/v1/messages",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            json=message_data
        )
        return response.status_code == 201
    except:
        return False

def send_message(content: str, customer_id: str, conversation_id: str) -> Dict[str, Any]:
    """Send a message and return the response."""
    message_id = str(uuid.uuid4())
    
    # Create message in database first to avoid foreign key constraint
    print(f"   Creating message in DB...")
    if not create_message_in_db(message_id, content, customer_id, conversation_id):
        print(f"   ⚠️ Could not create message in DB, proceeding anyway")
    
    payload = {
        "message_id": message_id,
        "customer_id": customer_id,
        "conversation_id": conversation_id,
        "content": content,
        "distributor_id": DISTRIBUTOR_ID,
        "channel": "WHATSAPP"
    }
    
    print(f"📨 Sending: '{content}'")
    
    try:
        response = requests.post(
            f"{AI_AGENT_URL}/process-message",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45  # Longer timeout for OpenAI calls
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ success={result['success']}, intent={result.get('intent')}, order_created={result.get('order_created')}, order_id={result.get('order_id')}")
            return result
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return {"success": False, "error": str(e)}

def test_basic_continuation():
    """Test the core continuation functionality."""
    print("🧪 FOCUSED CONTINUATION TEST")
    print("=" * 50)
    
    # Use existing customer/conversation from logs
    customer_id = "d0ad369e-8d92-4b1b-80ed-2fda2bab9be0"
    conversation_id = "56d78925-2a57-4ff8-93dd-27e5557d0d8c"
    
    print("\\nStep 1: Send initial order...")
    result1 = send_message("Quiero 2 leches", customer_id, conversation_id)
    
    if not result1.get('success'):
        print("❌ FAILED: Initial message failed")
        return False
    
    order1_id = result1.get('order_id')
    order1_created = result1.get('order_created')
    
    print(f"   Order 1 ID: {order1_id}, Created: {order1_created}")
    
    print("\\nStep 2: Send continuation message...")
    time.sleep(2)  # Small delay
    result2 = send_message("También 3 cocas", customer_id, conversation_id)
    
    if not result2.get('success'):
        print("❌ FAILED: Continuation message failed")
        return False
    
    order2_id = result2.get('order_id')
    order2_created = result2.get('order_created')
    
    print(f"   Order 2 ID: {order2_id}, Created: {order2_created}")
    
    # Analyze results
    print("\\n📊 ANALYSIS:")
    
    if order1_id and order2_id:
        if order1_id == order2_id:
            print("✅ SUCCESS: Both messages used the same order!")
            print(f"   Shared Order ID: {order1_id}")
            return True
        else:
            print("❌ FAILED: Different orders were created")
            print(f"   Order 1: {order1_id}")
            print(f"   Order 2: {order2_id}")
            return False
    elif order1_id and not order2_id:
        if result2.get('order_created') == False:
            print("✅ SUCCESS: Continuation worked - second message added to first order")
            print(f"   Original Order: {order1_id}")
            print("   Second message added to existing order (no new order created)")
            return True
        else:
            print("⚠️ UNCLEAR: First order created, second message unclear")
            return False
    else:
        print("❌ FAILED: Missing order information")
        print(f"   Order 1: {order1_id}, Order 2: {order2_id}")
        return False

def main():
    """Run the focused test."""
    
    # Check API health
    try:
        response = requests.get(f"{AI_AGENT_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API not available")
            return
    except:
        print("❌ Cannot connect to API")
        return
    
    print("✅ API is available")
    
    # Run the test
    success = test_basic_continuation()
    
    print("\\n" + "=" * 50)
    if success:
        print("🎉 CONTINUATION TEST PASSED!")
        print("   Multiple messages are correctly building a single order")
    else:
        print("❌ CONTINUATION TEST FAILED!")
        print("   Check server logs for debugging information")
        print("   Command: tail -f server.log")

if __name__ == "__main__":
    main()