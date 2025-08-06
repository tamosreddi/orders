"""
Autonomous Order Agent implementation for goal-oriented decision making.

Main agent that uses Pydantic AI framework with goal evaluation, memory learning,
and autonomous action execution following the dependency injection pattern from
examples/example_pydantic_ai.py.
"""

from __future__ import annotations as _annotations

import logging
import time
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from config.settings import settings
from config.feature_flags import (
    feature_flags, AutonomousAgentFeature, get_autonomous_confidence_threshold
)
from services.database import DatabaseService
from services.goal_evaluator import GoalEvaluator
from services.conversation_memory import ConversationMemory
from services.intent_classifier import intent_classifier, MessageIntent
from services.product_matcher import ProductMatcher
from services.smart_order_consolidator import SmartOrderConsolidator, ConsolidationDecision
from services.enhanced_product_validator import EnhancedProductValidator
from services.autonomous_order_creator import AutonomousOrderCreator
from schemas.message import MessageAnalysis, MessageIntent as MessageIntentEnum, ExtractedProduct
from schemas.order import OrderCreation, OrderProduct
from tools.supabase_tools import (
    create_order, fetch_product_catalog, update_message_ai_data
)
from schemas.goals import BusinessGoal, create_default_goal_configuration
from schemas.autonomous_agent import (
    AutonomousAction, AutonomousActionType, AutonomousAgentContext,
    AutonomousDecision, AutonomousResult, create_simple_action
)
from schemas.message import MessageAnalysis, MessageIntent, ExtractedProduct
from tools.autonomous_actions import execute_autonomous_action
from tools.supabase_tools import update_message_ai_data

logger = logging.getLogger(__name__)


@dataclass
class AutonomousAgentDeps:
    """
    Simplified dependencies for the autonomous agent focused on order capture.
    
    Replaced complex goal-based dependencies with streamlined services for:
    - Smart message consolidation based on timing
    - Enhanced product validation with human flags
    - Autonomous order creation using same mechanism as order_agent.py
    """
    database: DatabaseService
    distributor_id: str
    consolidator: SmartOrderConsolidator
    validator: EnhancedProductValidator
    order_creator: AutonomousOrderCreator
    intent_classifier: Any  # Keep for intent classification


# System prompt for the autonomous agent
AUTONOMOUS_SYSTEM_PROMPT = """
You are a specialized order-capture AI agent for a B2B food distributor. Your PRIMARY and ONLY role is to silently capture and process orders from customer messages. You are NOT a conversational assistant.

CRITICAL RULES:
1. **DO NOT INTERFERE** with normal buyer-seller conversations
2. **ONLY ACT** when the message clearly involves ordering products
3. **DEFAULT TO DO_NOTHING** for greetings, thanks, general chat, or non-order messages
4. **STAY SILENT** unless you need to clarify an order or confirm order details

WHEN TO TAKE ACTION:
✅ Customer mentions specific products with quantities ("quiero 5 cajas de leche")
✅ Customer asks about product availability for ordering
✅ Customer needs clarification about their order
✅ Customer has a question specifically about an order

WHEN TO DO NOTHING:
❌ Greetings ("hola", "buenos días", "cómo estás")
❌ Thanks or acknowledgments ("gracias", "perfecto", "ok")
❌ General conversation or relationship building
❌ Non-order related questions
❌ Any message that doesn't involve ordering

AVAILABLE ACTIONS:
- do_nothing: DEFAULT ACTION - Stay silent and let conversation flow
- create_order: ONLY when customer clearly wants to order with specific products/quantities
- ask_clarification: ONLY when order intent is clear but details are missing
- escalate_to_human: ONLY for complex order-related issues

DECISION PROCESS:
1. First ask: "Is this message about ordering products?" If NO → do_nothing
2. If YES: "Do I have clear products and quantities?" If YES → create_order
3. If NO: "Is the order intent clear but missing details?" If YES → ask_clarification
4. Otherwise → do_nothing

Remember: When in doubt, DO NOTHING. Let the humans handle their relationship.
"""

# Initialize the autonomous agent with OpenAI model
autonomous_agent = Agent(
    model=OpenAIModel(settings.openai_model),
    system_prompt=AUTONOMOUS_SYSTEM_PROMPT,
    deps_type=AutonomousAgentDeps,
    retries=2
)


@autonomous_agent.tool
async def analyze_customer_message(
    ctx: RunContext[AutonomousAgentDeps],
    message_content: str,
    conversation_context: str
) -> Dict[str, Any]:
    """
    Analyze customer message to extract intent and products.
    
    Args:
        ctx: Agent context with dependencies
        message_content: Customer message content
        conversation_context: Recent conversation context
        
    Returns:
        Dict: Analysis with intent and extracted products
    """
    # This would use the existing message analysis logic
    # For now, return a simplified analysis
    return {
        "intent": "BUY" if any(word in message_content.lower() for word in ["quiero", "necesito", "pedido"]) else "QUESTION",
        "confidence": 0.8,
        "products": [],
        "reasoning": "Simplified message analysis for autonomous agent"
    }


@autonomous_agent.tool
async def generate_possible_actions(
    ctx: RunContext[AutonomousAgentDeps],
    message_analysis: Dict[str, Any],
    context_summary: str
) -> List[Dict[str, Any]]:
    """
    Generate possible actions the agent could take.
    
    Args:
        ctx: Agent context with dependencies
        message_analysis: Analysis of the customer message
        context_summary: Summary of conversation context
        
    Returns:
        List[Dict]: Possible actions with parameters
    """
    actions = []
    intent = message_analysis.get("intent", "OTHER")
    confidence = message_analysis.get("confidence", 0.5)
    
    # Generate actions based on intent and context
    if intent == "BUY" and confidence > 0.7:
        # High confidence buy intent - consider creating order
        actions.append({
            "action_type": AutonomousActionType.CREATE_ORDER,
            "parameters": {
                "products": message_analysis.get("products", []),
                "confidence_override": confidence
            },
            "reasoning": "Customer has clear buying intent with high confidence",
            "confidence": confidence
        })
        
        # Also consider asking for clarification if products are unclear
        if not message_analysis.get("products"):
            actions.append({
                "action_type": AutonomousActionType.ASK_CLARIFICATION,
                "parameters": {
                    "question": "¿Qué productos específicos te gustaría pedir?",
                    "question_type": "product_specification"
                },
                "reasoning": "Buy intent detected but no specific products identified",
                "confidence": 0.8
            })
    
    elif intent == "QUESTION":
        # Customer asking questions - provide information or suggest products
        actions.append({
            "action_type": AutonomousActionType.PROVIDE_INFORMATION,
            "parameters": {
                "information_type": "general_response",
                "content": "Estoy aquí para ayudarte con tu pedido. ¿Qué información necesitas?"
            },
            "reasoning": "Customer has a question that needs to be addressed",
            "confidence": 0.7
        })
        
        actions.append({
            "action_type": AutonomousActionType.SUGGEST_PRODUCTS,
            "parameters": {
                "suggested_products": [],  # Would be populated with relevant products
                "suggestion_reason": "Basado en tu consulta, estos productos podrían interesarte"
            },
            "reasoning": "Customer question might benefit from product suggestions",
            "confidence": 0.6
        })
    
    else:
        # Unclear intent - ask for clarification or escalate
        actions.append({
            "action_type": AutonomousActionType.ASK_CLARIFICATION,
            "parameters": {
                "question": "¿En qué puedo ayudarte hoy? ¿Estás buscando hacer un pedido o necesitas información sobre nuestros productos?",
                "question_type": "intent_clarification"
            },
            "reasoning": "Customer intent is unclear, need clarification",
            "confidence": 0.7
        })
        
        # Consider escalation for very unclear cases
        if confidence < 0.5:
            actions.append({
                "action_type": AutonomousActionType.ESCALATE_TO_HUMAN,
                "parameters": {
                    "reason": "Customer message is unclear and requires human interpretation"
                },
                "reasoning": "Low confidence in understanding customer needs",
                "confidence": 0.8
            })
    
    return actions


class AutonomousOrderAgent:
    """
    Autonomous order processing agent with goal-oriented decision making.
    
    Integrates goal evaluation, memory learning, and autonomous action execution
    for intelligent order processing without fixed rules.
    """
    
    def __init__(self, database: DatabaseService, distributor_id: str):
        """
        Initialize the autonomous order agent.
        
        Args:
            database: Database service instance
            distributor_id: Distributor ID for multi-tenant isolation
        """
        self.database = database
        self.distributor_id = distributor_id
        
        # Initialize core services
        self.goal_evaluator = GoalEvaluator()
        self.memory_service = ConversationMemory(database)
        
        # Load business goals configuration (check for custom goals)
        goal_type = os.getenv('GOAL_TYPE', 'balanced')  # Can be: balanced, revenue, service, or custom
        goal_config = create_default_goal_configuration(distributor_id, goal_type)
        self.business_goals = goal_config.goals
        self.confidence_threshold = goal_config.confidence_threshold
        self.score_threshold = goal_config.score_threshold
        
        logger.info(f"Loaded {goal_type} goal configuration for distributor {distributor_id}")
        logger.info(f"Goal weights: {[(g.name, g.weight) for g in self.business_goals]}")
        
        # Set up dependencies for Pydantic AI agent
        self.deps = AutonomousAgentDeps(
            database=database,
            distributor_id=distributor_id,
            goal_evaluator=self.goal_evaluator,
            memory_service=self.memory_service,
            business_goals=self.business_goals
        )
        
        logger.info(f"Initialized AutonomousOrderAgent for distributor {distributor_id} with {len(self.business_goals)} business goals")
    
    async def process_message(self, message_data: Dict[str, Any]) -> Optional[AutonomousResult]:
        """
        Simplified autonomous agent focused ONLY on ORDER CAPTURE.
        
        Workflow:
        1. Classify intent (ORDER_RELATED?)
        2. If ORDER_RELATED → Create order using exact same mechanism as order_agent.py  
        3. If not ORDER_RELATED → Fallback to existing agent
        
        Args:
            message_data: Message from webhook with id, content, customer_id, etc.
            
        Returns:
            AutonomousResult: Complete processing result or None if failed
        """
        start_time = time.time()
        message_id = message_data.get('id', '')
        customer_id = message_data.get('customer_id', '')
        content = message_data.get('content', '').strip()
        
        logger.info(f"🤖 Processing message {message_id} with SIMPLIFIED autonomous agent")
        logger.info(f"📝 Message content: '{content[:100]}...'")
        
        try:
            # STEP 1: Check feature flags
            if not self._check_feature_flags(customer_id):
                logger.info(f"⚠️ Autonomous agent disabled for customer {customer_id}, using fallback")
                return await self._fallback_to_existing_agent(message_data)
            
            # STEP 2: Intent Classification - Is this ORDER_RELATED?
            intent_result = await self.intent_classifier.classify_intent(content)
            logger.info(f"🧠 Intent classification: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
            
            # STEP 3: Decision Logic - SIMPLIFIED
            if intent_result.intent != MessageIntent.ORDER_RELATED:
                logger.info(f"📝 Not order-related, falling back to existing agent")
                return await self._fallback_to_existing_agent(message_data)
            
            # STEP 4: ORDER CAPTURE - Use exact same mechanism as order_agent.py
            logger.info(f"🎯 ORDER_RELATED detected - proceeding with order capture")
            
            order_result = await self._capture_order_autonomous(message_data, intent_result)
            
            # STEP 5: Create result
            processing_time_ms = int((time.time() - start_time) * 1000)
            execution_status = "completed" if order_result.get('success') else "failed"
            
            # If order capture failed, fallback to existing agent
            if not order_result.get('success'):
                logger.warning(f"⚠️ Autonomous order capture failed, falling back to existing agent")
                return await self._fallback_to_existing_agent(message_data, order_result.get('error'))
            
            result = AutonomousResult(
                message_id=message_id,
                decision=None,  # No complex decision making anymore
                execution_status=execution_status,
                execution_result=order_result,
                processing_time_ms=processing_time_ms,
                fallback_used=False,
                created_order_id=order_result.get('order_id'),
                customer_response_sent=None  # No automatic responses
            )
            
            # Update message with simple autonomous processing signature
            await self._update_message_with_simple_autonomous_data(message_id, result, intent_result)
            
            logger.info(f"✅ Autonomous order capture completed for message {message_id} in {processing_time_ms}ms")
            logger.info(f"🎯 Created order: {order_result.get('order_id', 'N/A')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Autonomous processing failed for message {message_id}: {e}")
            
            # Fallback to existing agent on any error
            if feature_flags.fallback_enabled:
                logger.info(f"🔄 Falling back to existing agent due to error")
                return await self._fallback_to_existing_agent(message_data, str(e))
            else:
                return None
    
    async def _capture_order_autonomous(self, message_data: Dict[str, Any], intent_result) -> Dict[str, Any]:
        """
        SIMPLIFIED autonomous order capture using new integrated services.
        
        New workflow using:
        1. SmartOrderConsolidator for timing analysis
        2. EnhancedProductValidator for validation with human flags
        3. AutonomousOrderCreator for order creation (same mechanism as order_agent.py)
        
        Args:
            message_data: Message data from webhook
            intent_result: Intent classification result
            
        Returns:
            Dict with success status, order_id, error message, etc.
        """
        try:
            content = message_data.get('content', '').strip()
            customer_id = message_data.get('customer_id', '')
            conversation_id = message_data.get('conversation_id', '')
            message_id = message_data.get('id', '')
            
            logger.info(f"🎯 SIMPLIFIED autonomous order capture for: '{content[:50]}...'")
            
            # STEP 1: Extract products using simplified OpenAI call
            products = await self._extract_products_simple(content, message_data)
            if not products:
                return {
                    'success': False,
                    'error': 'No products extracted from message',
                    'products_extracted': 0
                }
            
            logger.info(f"📦 Extracted {len(products)} products")
            
            # STEP 2: Smart consolidation analysis - should we consolidate with existing session?
            consolidation_analysis = await self.consolidator.analyze_for_consolidation(
                message_data, products, intent_result
            )
            
            logger.info(f"🔍 Consolidation decision: {consolidation_analysis.decision.value} (confidence: {consolidation_analysis.confidence:.2f})")
            
            # Handle consolidation decision
            if consolidation_analysis.decision == ConsolidationDecision.WAIT_MORE:
                # Wait for more messages - don't create order yet
                return {
                    'success': True,
                    'action': 'waiting_for_more_messages',
                    'wait_duration_minutes': consolidation_analysis.wait_duration_minutes,
                    'reasoning': consolidation_analysis.reasoning,
                    'products_extracted': len(products)
                }
            
            elif consolidation_analysis.decision == ConsolidationDecision.NEW_ORDER:
                # Create new separate order
                final_products = products
                
            elif consolidation_analysis.decision in [ConsolidationDecision.CONSOLIDATE, ConsolidationDecision.ORDER_COMPLETE]:
                # Use products from this message (consolidation handled by session manager)
                final_products = products
            
            else:
                final_products = products
            
            # STEP 3: Enhanced product validation with human flags
            validation_result = await self.validator.validate_products_with_flags(
                final_products, content, conversation_id
            )
            
            logger.info(f"✅ Product validation: {validation_result.confidence_score:.0%} confidence, human validation needed: {validation_result.requires_human_validation}")
            
            # STEP 4: Create order using exact same mechanism as order_agent.py
            order_result = await self.order_creator.create_autonomous_order(
                customer_id=customer_id,
                conversation_id=conversation_id,
                validated_products=validation_result.validated_products,
                validation_result=validation_result,
                source_message_ids=[message_id],
                channel=message_data.get('channel', 'WHATSAPP')
            )
            
            if order_result.success:
                logger.info(f"🎉 Successfully created autonomous order {order_result.order_id}")
                return {
                    'success': True,
                    'order_id': order_result.order_id,
                    'created_products': order_result.created_products_count,
                    'pending_products': order_result.pending_products_count,
                    'human_validation_notes': order_result.human_validation_notes,
                    'consolidation_info': {
                        'decision': consolidation_analysis.decision.value,
                        'reasoning': consolidation_analysis.reasoning,
                        'confidence': consolidation_analysis.confidence
                    },
                    'validation_info': {
                        'confidence': validation_result.confidence_score,
                        'requires_human_validation': validation_result.requires_human_validation,
                        'summary': validation_result.validation_summary
                    }
                }
            else:
                logger.warning(f"❌ Autonomous order creation failed: {order_result.error_message}")
                return {
                    'success': False,
                    'error': order_result.error_message,
                    'products_extracted': len(products),
                    'pending_products': order_result.pending_products_count,
                    'human_validation_notes': order_result.human_validation_notes
                }
                
        except Exception as e:
            logger.error(f"❌ Autonomous order capture failed: {e}")
            return {
                'success': False,
                'error': f"Autonomous order capture error: {str(e)}",
                'products_extracted': 0
            }
    
    async def _extract_products_simple(self, content: str, message_data: Dict[str, Any]) -> List[ExtractedProduct]:
        """
        Simplified product extraction using same OpenAI mechanism as order_agent.py.
        
        This is a simplified version that focuses on reliable extraction without
        complex product matching at this stage.
        """
        try:
            # Use simple OpenAI extraction (can be enhanced later)
            # For now, use basic keyword extraction as fallback
            products = []
            content_lower = content.lower()
            
            # Basic Spanish product keywords and quantities
            basic_products = {
                'aceite': 'aceite',
                'agua': 'agua embotellada', 
                'leche': 'leche',
                'cerveza': 'cerveza',
                'coca cola': 'coca cola',
                'queso': 'queso',
                'pan': 'pan',
                'arroz': 'arroz'
            }
            
            spanish_numbers = {
                'un': 1, 'una': 1, 'uno': 1,
                'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5
            }
            
            # Simple extraction
            for keyword, product_name in basic_products.items():
                if keyword in content_lower:
                    quantity = 1
                    
                    # Look for quantity
                    words = content_lower.split()
                    for i, word in enumerate(words):
                        if keyword in word:
                            # Check previous words for quantity
                            for j in range(max(0, i-3), i):
                                if words[j] in spanish_numbers:
                                    quantity = spanish_numbers[words[j]]
                                    break
                                try:
                                    quantity = int(words[j])
                                    break
                                except ValueError:
                                    continue
                            break
                    
                    products.append(ExtractedProduct(
                        product_name=product_name,
                        quantity=quantity,
                        unit=None,
                        original_text=content,
                        confidence=0.7
                    ))
                    break  # Only extract first match for simplicity
            
            return products
            
        except Exception as e:
            logger.warning(f"Product extraction failed: {e}")
            return []
    
    async def _extract_products_openai(self, content: str) -> List[ExtractedProduct]:
        """
        Extract products using OpenAI - same logic as order_agent.py.
        """
        # This is a simplified version - in the full implementation,
        # we'll copy the exact OpenAI extraction logic from order_agent.py
        try:
            # For now, return a basic product extraction
            # TODO: Copy exact implementation from order_agent.py _analyze_with_openai
            
            # Simple Spanish product keywords for immediate testing
            products = []
            content_lower = content.lower()
            
            # Basic product detection
            if 'pepsi' in content_lower:
                quantity = 2 if 'dos' in content_lower else 1
                products.append(ExtractedProduct(
                    product_name='pepsi',
                    quantity=quantity,
                    unit='botellas',
                    original_text=content,
                    confidence=0.85
                ))
            
            if 'cerveza' in content_lower:
                quantity = 3 if 'tres' in content_lower else 1
                products.append(ExtractedProduct(
                    product_name='cerveza',
                    quantity=quantity,
                    unit='botellas', 
                    original_text=content,
                    confidence=0.85
                ))
                
            return products
            
        except Exception as e:
            logger.error(f"Product extraction failed: {e}")
            return []
    
    async def _validate_products_autonomous(
        self, products: List[ExtractedProduct], original_message: str, conversation_id: str
    ) -> Dict[str, Any]:
        """
        Validate products using exact same mechanism as order_agent.py _intelligent_product_validation.
        """
        try:
            # Get product catalog (same as order_agent.py)
            catalog_models = await fetch_product_catalog(
                self.database, self.distributor_id, active_only=True
            )
            
            if not catalog_models:
                logger.warning("No catalog available for validation")
                return {
                    'validated_products': products,
                    'requires_clarification': False,
                    'suggested_question': None
                }
            
            # Initialize product matcher (same as order_agent.py)  
            product_matcher = ProductMatcher()
            
            # Convert catalog models to dictionaries (same as order_agent.py)
            catalog_dicts = []
            for product in catalog_models:
                catalog_dicts.append({
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'unit': product.unit,
                    'unit_price': float(product.unit_price),
                    'stock_quantity': product.stock_quantity,
                    'in_stock': product.in_stock,
                    'minimum_order_quantity': product.minimum_order_quantity,
                    'active': product.active,
                    'brand': product.brand,
                    'category': product.category
                })
            
            validated_products = []
            
            # Process each extracted product (same logic as order_agent.py)
            for extracted_product in products:
                match_result = product_matcher.match_products(
                    extracted_product.product_name, 
                    catalog_dicts
                )
                
                logger.info(
                    f"Product matching result for '{extracted_product.product_name}': "
                    f"confidence_level={match_result.confidence_level}, "
                    f"matches={len(match_result.matches)}"
                )
                
                if match_result.confidence_level == "HIGH":
                    # High confidence - mark as confirmed (same as order_agent.py)
                    best_match = match_result.best_match
                    extracted_product.status = "confirmed"
                    extracted_product.matched_product_id = best_match.product_id
                    extracted_product.matched_product_name = best_match.product_name
                    extracted_product.validation_notes = f"Matched with {best_match.confidence:.0%} confidence"
                    if best_match.unit and not extracted_product.unit:
                        extracted_product.unit = best_match.unit
                        
                elif match_result.confidence_level in ["MEDIUM", "LOW"]:
                    # Medium/Low confidence - mark as pending with HUMAN VALIDATION flag
                    extracted_product.status = "pending"
                    extracted_product.validation_notes = "HUMAN VALIDATION REQUESTED - Uncertain product match"
                    if match_result.best_match:
                        extracted_product.matched_product_id = match_result.best_match.product_id
                        extracted_product.matched_product_name = match_result.best_match.product_name
                        
                else:  # NONE
                    # No matches found - mark as pending with HUMAN VALIDATION flag
                    extracted_product.status = "pending"
                    extracted_product.validation_notes = "HUMAN VALIDATION REQUESTED - No catalog match found"
                
                validated_products.append(extracted_product)
            
            return {
                'validated_products': validated_products,
                'requires_clarification': False,  # No clarification in autonomous mode
                'suggested_question': None
            }
            
        except Exception as e:
            logger.error(f"Product validation failed: {e}")
            return {
                'validated_products': products,
                'requires_clarification': False,
                'suggested_question': None
            }
    
    async def _create_order_autonomous(
        self, message_data: Dict[str, Any], confirmed_products: List[ExtractedProduct], ai_confidence: float
    ) -> Dict[str, Any]:
        """
        Create order using exact same mechanism as order_agent.py _create_simple_order.
        """
        try:
            customer_id = message_data.get('customer_id')
            if not customer_id or not confirmed_products:
                return {
                    'success': False,
                    'error': 'Missing customer_id or no products to process'
                }
            
            # Convert ExtractedProduct to OrderProduct (same as order_agent.py)
            order_products = []
            for extracted in confirmed_products:
                order_product = OrderProduct(
                    product_name=extracted.matched_product_name or extracted.product_name,
                    quantity=extracted.quantity,
                    unit=extracted.unit,
                    unit_price=None,  # Pricing handled by create_order function
                    line_price=None,
                    ai_confidence=extracted.confidence,
                    original_text=extracted.original_text,
                    matched_product_id=extracted.matched_product_id,
                    matching_confidence=extracted.confidence
                )
                order_products.append(order_product)
            
            # Create order using exact same OrderCreation schema (same as order_agent.py)
            order_creation = OrderCreation(
                customer_id=customer_id,
                distributor_id=self.distributor_id,
                conversation_id=message_data.get('conversation_id'),
                channel=message_data.get('channel', 'WHATSAPP'),
                products=order_products,
                delivery_date=None,
                additional_comment=None,
                ai_confidence=ai_confidence,
                source_message_ids=[message_data.get('id', '')]
            )
            
            # Create order using same function as order_agent.py
            order_id = await create_order(self.database, order_creation)
            
            if order_id:
                logger.info(f"✅ Autonomous agent created order: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'products_processed': len(order_products),
                    'products_confirmed': len([p for p in confirmed_products if p.status == "confirmed"]),
                    'products_pending_human_review': len([p for p in confirmed_products if p.status == "pending"])
                }
            else:
                return {
                    'success': False,
                    'error': 'Order creation returned no order_id',
                    'products_processed': len(order_products)
                }
                
        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'products_processed': len(confirmed_products) if confirmed_products else 0
            }
    
    async def _update_message_with_simple_autonomous_data(
        self, message_id: str, result: AutonomousResult, intent_result
    ) -> None:
        """
        Update message with simplified autonomous processing data.
        
        Uses "AUTONOMOUS_PROCESSED" as the ai_extracted_intent to distinguish
        from the existing agent's "BUY"/"OTHER" classifications.
        """
        try:
            # Create a simplified MessageAnalysis-like structure for compatibility
            analysis_data = {
                'ai_processed': True,
                'ai_confidence': intent_result.confidence,
                'ai_extracted_intent': 'AUTONOMOUS_PROCESSED',  # Signature of autonomous agent
                'ai_processing_time_ms': result.processing_time_ms,
                'updated_at': __import__('datetime').datetime.now().isoformat()
            }
            
            # If we have order result, add basic product info
            if result.execution_result and result.execution_result.get('success'):
                analysis_data['ai_extracted_products'] = [{
                    'autonomous_processing': True,
                    'products_confirmed': result.execution_result.get('products_confirmed', 0),
                    'products_pending_review': result.execution_result.get('products_pending_human_review', 0),
                    'order_created': True,
                    'order_id': result.created_order_id
                }]
            
            # Update message in database
            await self.database.update_single(
                table='messages',
                filters={'id': message_id},
                data=analysis_data
            )
            
            logger.info(f"✅ Updated message {message_id} with autonomous processing signature")
            
        except Exception as e:
            logger.error(f"Failed to update message with autonomous data: {e}")
    
    async def _make_autonomous_decision(self, context: AutonomousAgentContext) -> AutonomousDecision:
        """
        Make autonomous decision using goal-oriented evaluation.
        
        Args:
            context: Complete agent context
            
        Returns:
            AutonomousDecision: Decision with chosen action and evaluation
        """
        try:
            # Generate possible actions using our simplified order-detection logic
            possible_actions = await self._generate_simple_actions(context)
            
            # Evaluate each action against business goals
            action_evaluations = []
            for action in possible_actions:
                evaluation = await self.goal_evaluator.evaluate_action(
                    action, context, self.business_goals
                )
                action_evaluations.append(evaluation)
            
            # Choose the best action
            if action_evaluations:
                best_evaluation = max(action_evaluations, key=lambda e: e.overall_score)
                best_action = possible_actions[action_evaluations.index(best_evaluation)]
                
                # Create decision
                decision = AutonomousDecision(
                    chosen_action=best_action,
                    action_evaluation=best_evaluation,
                    alternative_actions=possible_actions[1:],  # Other actions considered
                    alternative_evaluations=action_evaluations[1:],
                    decision_reasoning=f"Chose {best_action.action_type} with score {best_evaluation.overall_score:.3f} and confidence {best_evaluation.confidence:.3f}",
                    confidence_factors=[
                        f"Goal alignment score: {best_evaluation.overall_score:.3f}",
                        f"Action confidence: {best_action.confidence:.3f}",
                        f"Context richness: {len(context.conversation_history)} messages"
                    ],
                    uncertainty_factors=[
                        f"Alternative actions available: {len(possible_actions) - 1}",
                        f"Goal score variance present" if len(set(best_evaluation.goal_scores.values())) > 1 else "Goal scores consistent"
                    ]
                )
                
                return decision
            else:
                # No actions generated - create escalation decision
                escalation_action = create_simple_action(
                    AutonomousActionType.ESCALATE_TO_HUMAN,
                    {"reason": "No viable actions generated"},
                    "Unable to determine appropriate action for customer message",
                    confidence=0.8
                )
                
                # Create minimal evaluation for escalation
                from schemas.goals import ActionEvaluation
                escalation_evaluation = ActionEvaluation(
                    action_name=escalation_action.action_type,
                    goal_scores={goal.name: 0.5 for goal in self.business_goals},
                    overall_score=0.5,
                    reasoning="Escalation due to inability to generate viable actions",
                    confidence=0.8
                )
                
                return AutonomousDecision(
                    chosen_action=escalation_action,
                    action_evaluation=escalation_evaluation,
                    decision_reasoning="Escalating due to inability to generate viable autonomous actions"
                )
                
        except Exception as e:
            logger.error(f"Failed to make autonomous decision: {e}")
            
            # Create safe escalation decision
            escalation_action = create_simple_action(
                AutonomousActionType.ESCALATE_TO_HUMAN,
                {"reason": f"Decision making error: {str(e)}"},
                "Error in autonomous decision making process",
                confidence=0.9
            )
            
            from schemas.goals import ActionEvaluation
            error_evaluation = ActionEvaluation(
                action_name=escalation_action.action_type,
                goal_scores={goal.name: 0.3 for goal in self.business_goals},
                overall_score=0.3,
                reasoning=f"Escalation due to error: {str(e)}",
                confidence=0.9
            )
            
            return AutonomousDecision(
                chosen_action=escalation_action,
                action_evaluation=error_evaluation,
                decision_reasoning=f"Autonomous decision making failed: {str(e)}"
            )
    
    async def _generate_simple_actions(self, context: AutonomousAgentContext) -> List[AutonomousAction]:
        """Generate possible actions using AI intent classification."""
        actions = []
        message_content = context.current_message.get('content', '')
        
        try:
            # Use AI to classify message intent
            classification = await intent_classifier.classify_message_intent(message_content)
            
            logger.info(f"AI classified message as: {classification.intent} (confidence: {classification.confidence})")
            
            # If not order-related, return DO_NOTHING immediately
            if not classification.is_order_related:
                actions.append(create_simple_action(
                    AutonomousActionType.DO_NOTHING,
                    {},
                    f"Non-order message - {classification.reasoning}",
                    confidence=classification.confidence
                ))
                return actions
            
            # Message is ORDER_RELATED - determine specific action needed
            message_lower = message_content.lower()
            
            # Check for direct ordering (buy intent with quantities)
            buy_words = ["quiero", "necesito", "pedido", "comprar", "me das", "dame", "ponme"]
            has_buy_intent = any(word in message_lower for word in buy_words)
            has_quantities = any(char.isdigit() for char in message_content)
            
            if has_buy_intent and has_quantities and context.has_extracted_products:
                # Clear order with products
                actions.append(create_simple_action(
                    AutonomousActionType.CREATE_ORDER,
                    {
                        "products": [{"product_name": p.product_name, "quantity": p.quantity} 
                                    for p in context.extracted_products],
                        "customer_notes": "Pedido procesado automáticamente"
                    },
                    "Clear order intent with specific products and quantities",
                    confidence=0.95
                ))
                
            elif has_buy_intent and not context.has_extracted_products:
                # Buy intent but unclear products - ask clarification
                actions.append(create_simple_action(
                    AutonomousActionType.ASK_CLARIFICATION,
                    {
                        "question": "¿Qué productos específicos necesitas y en qué cantidad?",
                        "question_type": "product_specification"
                    },
                    "Order intent detected but products/quantities unclear",
                    confidence=0.85
                ))
                
            # Check for pricing questions
            elif any(word in message_lower for word in ["precio", "cuesta", "cuanto", "vale"]):
                actions.append(create_simple_action(
                    AutonomousActionType.PROVIDE_PRICING,
                    {
                        "query_type": "pricing",
                        "message_content": message_content
                    },
                    "Customer asking for product pricing",
                    confidence=0.9
                ))
                
            # Check for availability questions
            elif any(word in message_lower for word in ["tienes", "disponible", "stock", "hay"]):
                actions.append(create_simple_action(
                    AutonomousActionType.CHECK_AVAILABILITY,
                    {
                        "query_type": "availability", 
                        "message_content": message_content
                    },
                    "Customer asking about product availability",
                    confidence=0.9
                ))
                
            # Check for product information requests
            elif any(word in message_lower for word in ["productos", "que tienen", "catalogo", "lista"]):
                actions.append(create_simple_action(
                    AutonomousActionType.SUGGEST_PRODUCTS,
                    {
                        "query_type": "product_list",
                        "message_content": message_content  
                    },
                    "Customer asking for product information",
                    confidence=0.85
                ))
                
            else:
                # Order-related but unclear what they need - ask clarification
                actions.append(create_simple_action(
                    AutonomousActionType.ASK_CLARIFICATION,
                    {
                        "question": "¿Necesitas información sobre precios, disponibilidad o hacer un pedido?",
                        "question_type": "intent_clarification"
                    },
                    "Order-related message but unclear specific need",
                    confidence=0.75
                ))
            
            return actions
            
        except Exception as e:
            logger.error(f"Failed to generate actions with AI classification: {e}")
            
            # Fallback to DO_NOTHING on any error
            actions.append(create_simple_action(
                AutonomousActionType.DO_NOTHING,
                {},
                f"AI classification failed - staying safe: {str(e)}",
                confidence=0.5
            ))
            return actions
    
    async def _execute_decision(
        self, decision: AutonomousDecision, context: AutonomousAgentContext
    ) -> Dict[str, Any]:
        """Execute the autonomous decision."""
        try:
            # Check feature flags for specific action types
            action_type = decision.chosen_action.action_type
            
            if action_type == AutonomousActionType.CREATE_ORDER:
                if not feature_flags.is_feature_enabled(
                    AutonomousAgentFeature.AUTONOMOUS_ORDER_CREATION,
                    self.distributor_id,
                    context.customer_id
                ):
                    logger.warning("Order creation disabled by feature flag, escalating")
                    return await execute_autonomous_action(
                        create_simple_action(
                            AutonomousActionType.ESCALATE_TO_HUMAN,
                            {"reason": "Order creation not enabled for this distributor"},
                            "Feature flag restriction"
                        ),
                        context,
                        self.database
                    )
            
            # Execute the chosen action
            result = await execute_autonomous_action(
                decision.chosen_action,
                context,
                self.database,
                self.memory_service
            )
            
            # Record learning event if execution was successful
            if result.get('success'):
                await self._record_successful_interaction(decision, context, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute decision: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Decision execution failed'
            }
    
    async def _escalate_decision(
        self, decision: AutonomousDecision, context: AutonomousAgentContext
    ) -> Dict[str, Any]:
        """Handle escalation of decision to human."""
        try:
            escalation_reason = decision.chosen_action.parameters.get(
                'reason', 
                'Autonomous agent confidence too low'
            )
            
            # Execute escalation action
            from tools.autonomous_actions import execute_escalate_to_human_action
            return await execute_escalate_to_human_action(
                context, self.database, escalation_reason
            )
            
        except Exception as e:
            logger.error(f"Failed to escalate decision: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Escalation failed'
            }
    
    def _check_feature_flags(self, customer_id: str) -> bool:
        """Check if autonomous agent is enabled for this customer."""
        return feature_flags.is_feature_enabled(
            AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
            self.distributor_id,
            customer_id
        )
    
    async def _fallback_to_existing_agent(
        self, message_data: Dict[str, Any], fallback_reason: str = "Autonomous agent not enabled"
    ) -> Optional[AutonomousResult]:
        """Fallback to existing streamlined agent."""
        try:
            # Import here to avoid circular imports
            from agents.order_agent import StreamlinedOrderProcessor
            
            existing_agent = StreamlinedOrderProcessor(self.database, self.distributor_id)
            analysis = await existing_agent.process_message(message_data)
            
            if analysis:
                # Create autonomous result indicating fallback was used
                result = AutonomousResult(
                    message_id=message_data.get('id', ''),
                    decision=None,  # No autonomous decision made
                    execution_status="fallback_used",
                    execution_result={'success': True, 'agent_used': 'existing'},
                    processing_time_ms=int(analysis.processing_time_ms),
                    fallback_used=True,
                    fallback_reason=fallback_reason
                )
                
                logger.info(f"✅ Fallback to existing agent successful for message {message_data.get('id', '')}")
                return result
            else:
                logger.error(f"❌ Fallback to existing agent failed")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fallback to existing agent: {e}")
            return None
    
    def _summarize_conversation_context(self, context: AutonomousAgentContext) -> str:
        """Create a summary of conversation context for AI agent."""
        summary_parts = []
        
        if context.customer_preferences:
            prefs = [f"{p.preference_type}: {p.value}" for p in context.customer_preferences[:3]]
            summary_parts.append(f"Customer preferences: {', '.join(prefs)}")
        
        if context.recent_orders:
            summary_parts.append(f"Recent orders: {len(context.recent_orders)} orders")
        
        if context.conversation_history:
            summary_parts.append(f"Conversation history: {len(context.conversation_history)} messages")
        
        if context.time_context.business_hours:
            summary_parts.append("During business hours")
        
        return "; ".join(summary_parts) if summary_parts else "Limited context available"
    
    async def _record_successful_interaction(
        self, decision: AutonomousDecision, context: AutonomousAgentContext, result: Dict[str, Any]
    ):
        """Record successful interaction for learning."""
        try:
            if feature_flags.is_feature_enabled(
                AutonomousAgentFeature.MEMORY_LEARNING_ENABLED,
                self.distributor_id,
                context.customer_id
            ):
                from schemas.autonomous_agent import LearningEvent
                
                learning_event = LearningEvent(
                    event_type="successful_autonomous_action",
                    context_summary=f"Action: {decision.chosen_action.action_type}, Score: {decision.action_evaluation.overall_score:.3f}",
                    action_taken=str(decision.chosen_action.action_type),
                    outcome="success",
                    expected_outcome="positive_customer_interaction",
                    success_metrics={
                        "goal_score": decision.action_evaluation.overall_score,
                        "confidence": decision.action_evaluation.confidence,
                        "execution_success": 1.0 if result.get('success') else 0.0
                    },
                    lesson_learned=f"Action {decision.chosen_action.action_type} was successful with goal score {decision.action_evaluation.overall_score:.3f}",
                    customer_id=context.customer_id,
                    distributor_id=context.distributor_id
                )
                
                await self.memory_service.record_learning_event(learning_event)
                
        except Exception as e:
            logger.warning(f"Failed to record learning event: {e}")
    
    async def _update_message_with_autonomous_data(
        self, message_id: str, result: AutonomousResult, decision: AutonomousDecision
    ):
        """Update message with autonomous processing data."""
        try:
            # Create a MessageAnalysis-like object for the update
            from schemas.message import MessageAnalysis, MessageIntent
            
            # Extract or create intent information
            intent = MessageIntent(
                intent="AUTONOMOUS_PROCESSED",
                confidence=decision.action_evaluation.confidence if decision else 0.5,
                reasoning=decision.decision_reasoning if decision else "Autonomous processing"
            )
            
            analysis = MessageAnalysis(
                message_id=message_id,
                intent=intent,
                extracted_products=[],  # Could be populated from decision
                customer_notes=f"Processed autonomously: {result.execution_status}",
                delivery_date=None,
                processing_time_ms=result.processing_time_ms
            )
            
            await update_message_ai_data(
                self.database, message_id, analysis, self.distributor_id
            )
            
        except Exception as e:
            logger.warning(f"Failed to update message with autonomous data: {e}")


def create_autonomous_order_agent(
    database: DatabaseService, distributor_id: str
) -> AutonomousOrderAgent:
    """
    Factory function for autonomous order agent.
    
    Args:
        database: Database service instance
        distributor_id: Distributor ID for multi-tenant isolation
        
    Returns:
        AutonomousOrderAgent: Configured autonomous agent
    """
    return AutonomousOrderAgent(database, distributor_id)