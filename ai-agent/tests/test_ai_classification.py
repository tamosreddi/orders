#!/usr/bin/env python3
"""
Test script for AI-powered intent classification and autonomous agent.

Run this to verify the AI classification works correctly for various message types.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Add the ai-agent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.intent_classifier import intent_classifier, create_intent_classifier


async def test_intent_classification():
    """Test AI intent classification with various message types."""
    
    print("🧠 Testing AI Intent Classification")
    print("=" * 50)
    
    # Test messages - mix of ORDER_RELATED and NOT_ORDER_RELATED
    test_messages = [
        # NOT_ORDER_RELATED messages
        ("Hola", "NOT_ORDER_RELATED"),
        ("Buenos días", "NOT_ORDER_RELATED"),
        ("Gracias", "NOT_ORDER_RELATED"),
        ("Mi equipo favorito ganó anoche", "NOT_ORDER_RELATED"),
        ("Cómo estás?", "NOT_ORDER_RELATED"),
        ("Hace mucho calor hoy", "NOT_ORDER_RELATED"),
        ("Viste la serie de Netflix?", "NOT_ORDER_RELATED"),
        ("buenas buenas", "NOT_ORDER_RELATED"),
        
        # ORDER_RELATED messages
        ("Quiero 5 botellas de pepsi", "ORDER_RELATED"),
        ("Necesito 10 cajas de leche", "ORDER_RELATED"),
        ("Cuánto cuesta la leche?", "ORDER_RELATED"),
        ("Tienes cerveza disponible?", "ORDER_RELATED"),
        ("Qué productos tienen?", "ORDER_RELATED"),
        ("Hay stock de pan?", "ORDER_RELATED"),
        ("Precio del arroz por favor", "ORDER_RELATED"),
        ("Dame 3 cajas de agua", "ORDER_RELATED"),
        ("Cuántas unidades de azúcar puedo pedir?", "ORDER_RELATED")
    ]
    
    correct_predictions = 0
    total_predictions = len(test_messages)
    
    print("Testing each message:\n")
    
    for message, expected_intent in test_messages:
        try:
            result = await intent_classifier.classify_message_intent(message)
            
            # Check if classification is correct
            is_correct = result.intent.value == expected_intent
            correct_predictions += is_correct
            
            status = "✅" if is_correct else "❌"
            print(f"{status} '{message}'")
            print(f"   Expected: {expected_intent}")
            print(f"   Got: {result.intent.value} (confidence: {result.confidence:.2f})")
            print(f"   Reasoning: {result.reasoning}")
            print()
            
        except Exception as e:
            print(f"❌ '{message}' - ERROR: {e}")
            print()
    
    # Calculate accuracy
    accuracy = (correct_predictions / total_predictions) * 100
    
    print("=" * 50)
    print(f"📊 Classification Results:")
    print(f"   Correct: {correct_predictions}/{total_predictions}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("🎉 EXCELLENT: AI classification is working well!")
    elif accuracy >= 70:
        print("✅ GOOD: AI classification is acceptable")
    else:
        print("⚠️ NEEDS IMPROVEMENT: AI classification accuracy is low")
    
    return accuracy >= 70


async def test_autonomous_agent_simulation():
    """Simulate autonomous agent behavior without actually running it."""
    
    print("\n🤖 Simulating Autonomous Agent Behavior")
    print("=" * 50)
    
    test_scenarios = [
        ("Hola", "DO_NOTHING", "Agent should stay silent"),
        ("Quiero 5 pepsi", "CREATE_ORDER", "Agent should create order"),
        ("Cuánto cuesta leche?", "PROVIDE_PRICING", "Agent should provide pricing"),
        ("Tienes cerveza?", "CHECK_AVAILABILITY", "Agent should check availability"),
        ("Mi equipo ganó", "DO_NOTHING", "Agent should stay silent"),
        ("Qué productos tienes?", "SUGGEST_PRODUCTS", "Agent should list products")
    ]
    
    print("Expected agent behavior:\n")
    
    for message, expected_action, description in test_scenarios:
        try:
            classification = await intent_classifier.classify_message_intent(message)
            
            # Determine expected action based on classification
            if not classification.is_order_related:
                predicted_action = "DO_NOTHING"
            elif any(word in message.lower() for word in ["precio", "cuesta", "cuanto"]):
                predicted_action = "PROVIDE_PRICING"
            elif any(word in message.lower() for word in ["tienes", "disponible", "stock"]):
                predicted_action = "CHECK_AVAILABILITY"
            elif any(word in message.lower() for word in ["productos", "catalogo", "lista"]):
                predicted_action = "SUGGEST_PRODUCTS"
            elif any(word in message.lower() for word in ["quiero", "necesito", "dame"]):
                predicted_action = "CREATE_ORDER"
            else:
                predicted_action = "ASK_CLARIFICATION"
            
            status = "✅" if predicted_action == expected_action else "❌"
            print(f"{status} '{message}'")
            print(f"   Intent: {classification.intent.value}")
            print(f"   Expected Action: {expected_action}")
            print(f"   Predicted Action: {predicted_action}")
            print(f"   Description: {description}")
            print()
            
        except Exception as e:
            print(f"❌ '{message}' - ERROR: {e}")
            print()


async def main():
    """Main test function."""
    print("🚀 AI-Powered Autonomous Agent Test Suite")
    print("=" * 70)
    
    try:
        # Test intent classification
        classification_success = await test_intent_classification()
        
        # Test agent behavior simulation
        await test_autonomous_agent_simulation()
        
        print("=" * 70)
        print("📝 SUMMARY")
        print("=" * 70)
        
        if classification_success:
            print("✅ AI Intent Classification: WORKING")
            print("✅ Ready to test with real WhatsApp messages!")
            print("\n💡 Next steps:")
            print("   1. Restart your API: python3 api.py")
            print("   2. Send 'Hola' via WhatsApp → Should get NO response")
            print("   3. Send 'Cuánto cuesta leche?' → Should get pricing")
            print("   4. Send 'Quiero 5 pepsi' → Should create order")
        else:
            print("❌ AI Intent Classification: NEEDS WORK")
            print("   Check OpenAI API configuration and prompts")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        print("   Check your OpenAI API key and environment configuration")


if __name__ == "__main__":
    asyncio.run(main())