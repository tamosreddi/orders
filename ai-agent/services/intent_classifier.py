"""
AI-powered intent classification for autonomous order agent.

Uses OpenAI to determine if a message is ORDER_RELATED or NOT_ORDER_RELATED
with high accuracy and flexibility to handle any phrasing.
"""

from __future__ import annotations as _annotations

import logging
from typing import Dict, Any, Optional
from enum import Enum

from openai import AsyncOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)

# Set up OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class MessageIntent(str, Enum):
    """Binary intent classification for order capture."""
    ORDER_RELATED = "ORDER_RELATED"
    NOT_ORDER_RELATED = "NOT_ORDER_RELATED"


class IntentClassificationResult:
    """Result of intent classification with confidence."""
    
    def __init__(self, intent: MessageIntent, confidence: float, reasoning: str):
        self.intent = intent
        self.confidence = confidence
        self.reasoning = reasoning
        
    @property
    def is_order_related(self) -> bool:
        """Check if message is order-related."""
        return self.intent == MessageIntent.ORDER_RELATED
        
    @property
    def is_high_confidence(self) -> bool:
        """Check if classification is high confidence."""
        return self.confidence >= 0.8


class OrderIntentClassifier:
    """AI-powered classifier for order-related messages."""
    
    def __init__(self):
        """Initialize the intent classifier."""
        self.model = settings.openai_model
        
    async def classify_message_intent(
        self, 
        message_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentClassificationResult:
        """
        Classify if a message is order-related using AI.
        
        Args:
            message_content: The customer message to classify
            context: Optional conversation context
            
        Returns:
            IntentClassificationResult: Classification with confidence
        """
        try:
            # Build the classification prompt
            prompt = self._build_classification_prompt(message_content, context)
            
            # Call OpenAI for classification
            response = await self._call_openai_classification(prompt)
            
            # Parse the response
            result = self._parse_classification_response(response, message_content)
            
            logger.info(f"Intent classified: '{message_content[:50]}...' → {result.intent} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Default to NOT_ORDER_RELATED on error to avoid unwanted responses
            return IntentClassificationResult(
                intent=MessageIntent.NOT_ORDER_RELATED,
                confidence=0.5,
                reasoning=f"Classification failed: {str(e)}"
            )
    
    def _build_classification_prompt(self, message_content: str, context: Optional[Dict[str, Any]]) -> str:
        """Build the AI prompt for intent classification."""
        
        prompt = f"""You are an AI assistant that determines if customer messages are related to ordering products from a B2B food distributor.

CLASSIFICATION RULES:
- Return "ORDER_RELATED" if the message is about:
  * Placing orders ("quiero 5 pepsi", "necesito leche")
  * Product pricing ("cuánto cuesta la leche?", "precio del pan")
  * Product availability ("tienes cerveza?", "hay stock de leche?")
  * Product information ("qué tipos de leche tienen?", "productos disponibles")
  * Order modifications ("cambia mi pedido", "agrega 2 más")
  * Quantities ("cuántas cajas puedo pedir?")

- Return "NOT_ORDER_RELATED" if the message is about:
  * Greetings ("hola", "buenos días", "buenas buenas")
  * Thanks/acknowledgments ("gracias", "perfecto", "ok")
  * Personal conversation ("cómo estás?", "qué tal la familia?")
  * General topics ("mi equipo ganó", "hace calor", "viste la serie?")
  * Unrelated business ("horarios de atención", "dirección")

CUSTOMER MESSAGE: "{message_content}"

Respond in this exact JSON format:
{{
    "intent": "ORDER_RELATED" or "NOT_ORDER_RELATED",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification"
}}

Be conservative: when in doubt, classify as NOT_ORDER_RELATED."""

        return prompt
    
    async def _call_openai_classification(self, prompt: str) -> str:
        """Call OpenAI API for classification."""
        
        response = await openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a precise intent classifier for a B2B food distributor. Always respond with valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=150,
            timeout=10
        )
        
        return response.choices[0].message.content
    
    def _parse_classification_response(self, response: str, original_message: str) -> IntentClassificationResult:
        """Parse OpenAI response into classification result."""
        
        try:
            import json
            parsed = json.loads(response.strip())
            
            intent_str = parsed.get("intent", "NOT_ORDER_RELATED")
            confidence = float(parsed.get("confidence", 0.5))
            reasoning = parsed.get("reasoning", "AI classification")
            
            # Validate intent
            if intent_str not in ["ORDER_RELATED", "NOT_ORDER_RELATED"]:
                intent_str = "NOT_ORDER_RELATED"
                
            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))
            
            intent = MessageIntent(intent_str)
            
            return IntentClassificationResult(intent, confidence, reasoning)
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse classification response: {e}. Response: {response}")
            
            # Fallback: simple keyword check
            message_lower = original_message.lower()
            order_keywords = ["quiero", "necesito", "pedido", "precio", "cuesta", "tienes", "disponible", "stock"]
            
            if any(keyword in message_lower for keyword in order_keywords):
                return IntentClassificationResult(
                    intent=MessageIntent.ORDER_RELATED,
                    confidence=0.6,
                    reasoning="Fallback keyword detection"
                )
            else:
                return IntentClassificationResult(
                    intent=MessageIntent.NOT_ORDER_RELATED,
                    confidence=0.7,
                    reasoning="Fallback keyword detection - no order keywords found"
                )


def create_intent_classifier() -> OrderIntentClassifier:
    """Factory function to create intent classifier."""
    return OrderIntentClassifier()


# Global instance
intent_classifier = create_intent_classifier()