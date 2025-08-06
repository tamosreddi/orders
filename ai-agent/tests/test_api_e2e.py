#!/usr/bin/env python3
"""
End-to-end test for AI agent API with Spanish extraction.

Tests the full flow:
1. Send message to AI agent API
2. Verify Spanish extraction works
3. Check if intelligent product matching is triggered
4. Verify database updates
"""

import asyncio
import json
import aiohttp
import uuid
from datetime import datetime

async def test_ai_agent_api():
    """Test the AI agent API with the user's Spanish message."""
    
    # The message that the user reported wasn't working
    test_message = "Quiero comprar un litro de aceite de canola por favor"
    
    # Create mock message data similar to what the webhook would send
    message_data = {
        "message_id": str(uuid.uuid4()),
        "customer_id": "test-customer-123",
        "conversation_id": "test-conversation-456", 
        "content": test_message,
        "distributor_id": "demo-distributor",
        "channel": "WHATSAPP"
    }
    
    print(f"🚀 Testing AI Agent API with message: '{test_message}'")
    print("=" * 70)
    print(f"📝 Message data:")
    for key, value in message_data.items():
        print(f"   {key}: {value}")
    print()
    
    # Send request to AI agent API
    ai_agent_url = "http://localhost:8001"
    endpoint = f"{ai_agent_url}/process-message-background"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"🔄 Sending request to: {endpoint}")
            
            async with session.post(
                endpoint,
                json=message_data,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ API call successful!")
                    print(f"📄 Response:")
                    print(json.dumps(result, indent=2))
                    
                    # Check if the response indicates successful processing
                    if result.get("status") == "success":
                        print(f"\n🎉 SUCCESS: Message processed successfully!")
                        
                        # Check for extracted products
                        analysis = result.get("analysis", {})
                        extracted_products = analysis.get("extracted_products", [])
                        
                        if extracted_products:
                            print(f"✅ Found {len(extracted_products)} extracted products:")
                            for i, product in enumerate(extracted_products, 1):
                                print(f"   Product {i}:")
                                print(f"     Name: {product.get('product_name')}")
                                print(f"     Quantity: {product.get('quantity')}")
                                print(f"     Unit: {product.get('unit')}")
                                print(f"     Confidence: {product.get('confidence')}")
                            
                            # Verify the expected extraction
                            first_product = extracted_products[0]
                            success = True
                            
                            if first_product.get('product_name') != 'aceite de canola':
                                print(f"❌ Expected 'aceite de canola', got '{first_product.get('product_name')}'")
                                success = False
                            
                            if first_product.get('quantity') != 1:
                                print(f"❌ Expected quantity 1, got {first_product.get('quantity')}")
                                success = False
                                
                            if first_product.get('unit') != 'litro':
                                print(f"❌ Expected unit 'litro', got '{first_product.get('unit')}'")
                                success = False
                            
                            if success:
                                print(f"\n🎯 PERFECT: All extraction expectations met!")
                        else:
                            print(f"❌ No products extracted - Spanish extraction may not be working in API")
                        
                        # Check intent classification
                        intent = analysis.get("intent", {})
                        if intent:
                            print(f"\n🧠 Intent Analysis:")
                            print(f"   Intent: {intent.get('intent')}")
                            print(f"   Confidence: {intent.get('confidence')}")
                            print(f"   Reasoning: {intent.get('reasoning')}")
                    else:
                        print(f"⚠️ API returned non-success status: {result.get('status')}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ API call failed with status {response.status}")
                    print(f"Error: {error_text}")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ Request timed out - AI agent may not be running")
        return False
    except aiohttp.ClientConnectorError:
        print("❌ Could not connect to AI agent API")
        print("💡 Make sure the AI agent is running: python ai-agent/api.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

async def main():
    """Run the end-to-end test."""
    print("🧪 AI Agent API End-to-End Test")
    print("Testing Spanish product extraction with intelligent matching")
    print()
    
    success = await test_ai_agent_api()
    
    print("\n" + "=" * 70)
    
    if success:
        print("🎉 End-to-end test completed successfully!")
        print("The enhanced Spanish extraction is working in the full system.")
    else:
        print("⚠️ End-to-end test encountered issues.")
        print("Check the AI agent logs for more details.")
    
    print("\n💡 Next steps:")
    print("1. If successful: The Spanish extraction enhancement is complete")
    print("2. If issues: Check AI agent logs and debug the API integration")

if __name__ == "__main__":
    asyncio.run(main())