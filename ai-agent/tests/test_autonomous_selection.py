#!/usr/bin/env python3
"""
Test script to verify autonomous agent selection.

Run this script to confirm that the autonomous agent is being selected
instead of the streamlined agent when feature flags are enabled.
"""

import asyncio
import sys
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

print(f"🔧 Loading environment from: {env_path}")
print(f"🔧 USE_AUTONOMOUS_AGENT = {os.getenv('USE_AUTONOMOUS_AGENT')}")

# Add the ai-agent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.feature_flags import feature_flags, is_autonomous_agent_enabled
from agents.agent_factory import create_agent_factory
from services.database import DatabaseService


async def test_autonomous_agent_selection():
    """Test that autonomous agent is being selected correctly."""
    
    print("🧪 Testing Autonomous Agent Selection")
    print("=" * 50)
    
    # Test environment variables loading
    print(f"✅ Global autonomous enabled: {feature_flags.global_autonomous_enabled}")
    print(f"✅ Fallback enabled: {feature_flags.fallback_enabled}")
    print(f"✅ Testing mode: {feature_flags.testing_mode}")
    print()
    
    # Test feature flag evaluation
    test_distributor = "550e8400-e29b-41d4-a716-446655440000"  # Your demo distributor
    test_customer = "test_customer_123"
    
    is_enabled = is_autonomous_agent_enabled(test_distributor, test_customer)
    print(f"✅ Autonomous agent enabled for distributor {test_distributor}: {is_enabled}")
    
    if not is_enabled:
        print("❌ ERROR: Autonomous agent is NOT enabled!")
        print("   Check your environment variables in .env file")
        return False
    
    # Test agent factory selection
    try:
        print("\n🏭 Testing Agent Factory Selection")
        print("-" * 30)
        
        db = DatabaseService()
        factory = create_agent_factory(db, test_distributor)
        
        # Create agent and check type
        agent = await factory.create_agent(test_customer)
        agent_type = type(agent).__name__
        
        print(f"✅ Selected agent type: {agent_type}")
        
        if agent_type == "AutonomousOrderAgent":
            print("🎉 SUCCESS: Autonomous agent is being selected!")
            
            # Test agent capabilities
            from agents.agent_factory import AgentType
            capabilities = factory.get_agent_capabilities(AgentType.AUTONOMOUS)
            print(f"✅ Agent capabilities: {capabilities['name']}")
            print(f"✅ Features: {len(capabilities['features'])} available")
            
            return True
        else:
            print(f"❌ ERROR: Expected AutonomousOrderAgent, got {agent_type}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to test agent selection: {e}")
        return False


async def test_message_processing_simulation():
    """Simulate message processing to verify autonomous agent usage."""
    
    print("\n📨 Testing Message Processing Simulation")
    print("-" * 40)
    
    try:
        test_distributor = "550e8400-e29b-41d4-a716-446655440000"
        db = DatabaseService()
        factory = create_agent_factory(db, test_distributor)
        
        # Simulate a typical order message
        test_message = {
            "id": "test_msg_123",
            "content": "quiero dos botellas de leche por favor",
            "customer_id": "test_customer_123",
            "conversation_id": "test_conv_123",
            "channel": "WHATSAPP"
        }
        
        print(f"✅ Test message: '{test_message['content']}'")
        
        # Get the agent that would be used
        agent = await factory.create_agent(test_message["customer_id"])
        agent_type = type(agent).__name__
        
        print(f"✅ Agent selected for processing: {agent_type}")
        
        if agent_type == "AutonomousOrderAgent":
            print("🎉 SUCCESS: Message would be processed by Autonomous Agent!")
            
            # Show agent health status
            health = await factory.get_agent_health_status()
            print(f"✅ Factory status: {health['factory_status']}")
            print(f"✅ Autonomous agent available: {health['agents']['autonomous']['available']}")
            
            return True
        else:
            print(f"❌ ERROR: Message would be processed by {agent_type} instead of AutonomousOrderAgent")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to simulate message processing: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Autonomous Agent Configuration Test")
    print("=" * 60)
    
    # Run all tests
    selection_test = await test_autonomous_agent_selection()
    processing_test = await test_message_processing_simulation()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if selection_test and processing_test:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Autonomous agent is configured correctly")
        print("✅ Your system will use the autonomous agent 100%")
        print("\n💡 Next steps:")
        print("   1. Start your AI agent server: cd ai-agent && python main.py")
        print("   2. Send test messages via WhatsApp or API")
        print("   3. Check logs for autonomous agent processing")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Check the error messages above and fix configuration")
        
        if not selection_test:
            print("   - Fix environment variables in .env file")
        if not processing_test:
            print("   - Check agent factory configuration")


if __name__ == "__main__":
    asyncio.run(main())