"""
Session-Aware Order Agent for Multi-Message Order Processing

This enhanced order agent can handle orders that span multiple messages within a conversation.
It uses the Order Session Manager and Pattern Detector to:
1. Detect when to start order sessions
2. Collect messages across multiple interactions
3. Consolidate orders when conversation is complete

Author: AI Assistant
Date: 2025-08-04
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from config.settings import settings
from services.database import DatabaseService
from services.order_session_manager import OrderSessionManager, SessionStatus
from services.pattern_detector import PatternDetector
from services.product_matcher import ProductMatcher
from schemas.message import MessageAnalysis, MessageIntent, ExtractedProduct
from schemas.order import OrderCreation, OrderProduct
from tools.supabase_tools import (
    get_recent_messages_for_context,
    update_message_ai_data,
    create_order,
    fetch_product_catalog
)

logger = logging.getLogger(__name__)


@dataclass
class SessionAwareDeps:
    """Dependencies for session-aware order processing."""
    database: DatabaseService
    distributor_id: str
    session_manager: OrderSessionManager
    pattern_detector: PatternDetector
    product_matcher: ProductMatcher


# Enhanced system prompt for session-aware processing
SESSION_AWARE_SYSTEM_PROMPT = """
You are an AI assistant for a B2B food distributor processing WhatsApp orders in Spanish and English.

Your job is to analyze customer messages in the context of ongoing conversations and extract order information.

IMPORTANT: You are part of a multi-message order collection system. This message may be:
- The start of a new order
- Additional items to an existing order
- Corrections to previous items
- Confirmation that the order is complete

INTENT CLASSIFICATION:
- BUY: Customer wants to purchase products (e.g., "quiero", "necesito", "dame")
- MODIFY: Customer is changing/correcting previous items
- CONFIRM: Customer is confirming the current order is complete
- QUESTION: Customer asking about products/services  
- OTHER: General conversation or greetings

PRODUCT EXTRACTION:
For BUY and MODIFY intents, extract all products with quantities and units.

Return in this JSON format:
```json
{
  "intent": "BUY",
  "confidence": 0.85,
  "reasoning": "Customer expressing purchase intent",
  "session_action": "START_OR_CONTINUE",
  "products": [
    {
      "name": "aceite de canola",
      "quantity": 1,
      "unit": "litro",
      "original_text": "un litro de aceite de canola",
      "confidence": 0.8
    }
  ]
}
```

SESSION_ACTION can be:
- START_OR_CONTINUE: This message should start or continue an order session
- MODIFY_EXISTING: This message modifies items from previous messages
- CLOSE_SESSION: This message indicates the order is complete
- NO_ACTION: This message doesn't affect the order session

IMPORTANT: Always extract the exact product name as mentioned by the customer.
"""

# Initialize session-aware agent
session_aware_agent = Agent(
    model=OpenAIModel(settings.openai_model),
    system_prompt=SESSION_AWARE_SYSTEM_PROMPT,
    deps_type=SessionAwareDeps,
    retries=2
)


class SessionAwareOrderProcessor:
    """
    Enhanced order processor that handles multi-message order sessions.
    
    Workflow:
    1. Analyze message with AI and pattern detection
    2. Check for active order session
    3. Start new session or add to existing session
    4. Extract and collect items across messages
    5. Detect closing patterns and consolidate order
    6. Create final order when session is complete
    """
    
    def __init__(self, database: DatabaseService, distributor_id: str):
        """Initialize the session-aware order processor."""
        self.database = database
        self.distributor_id = distributor_id
        self.session_manager = OrderSessionManager(database)
        self.pattern_detector = PatternDetector()
        self.product_matcher = ProductMatcher()
        
        self.deps = SessionAwareDeps(
            database=database,
            distributor_id=distributor_id,
            session_manager=self.session_manager,
            pattern_detector=self.pattern_detector,
            product_matcher=self.product_matcher
        )
        
        logger.info(f"Initialized SessionAwareOrderProcessor for distributor {distributor_id}")
    
    async def process_message(self, message_data: Dict[str, Any]) -> Optional[MessageAnalysis]:
        """
        Process message through session-aware workflow.
        
        Args:
            message_data: Message from webhook with id, content, customer_id, etc.
            
        Returns:
            MessageAnalysis if successful, None if failed
        """
        start_time = time.time()
        message_id = message_data.get('id', '')
        content = message_data.get('content', '').strip()
        conversation_id = message_data.get('conversation_id', '')
        
        logger.info(f"🔄 Processing message {message_id} with session awareness: '{content[:50]}...'")
        
        try:
            # STEP 1: Clean up expired sessions first
            await self._cleanup_expired_sessions()
            
            # STEP 2: Pattern analysis for session management
            pattern_analysis = self.pattern_detector.analyze_message_context(content)
            logger.info(f"Pattern analysis: {pattern_analysis['suggested_action']} (confidence: {pattern_analysis['overall_confidence']:.2f})")
            
            # STEP 3: Check for active session
            active_session = self.session_manager.get_active_session(conversation_id)
            
            # STEP 4: AI analysis with session context
            session_context = await self._get_session_context(conversation_id, active_session)
            analysis_result = await self._analyze_with_ai(content, session_context)
            
            if not analysis_result:
                logger.error(f"❌ Failed to analyze message {message_id}")
                return None
            
            intent, products, session_action = analysis_result
            
            # STEP 5: Session management based on pattern analysis and AI
            session_result = await self._manage_session(
                message_data, active_session, pattern_analysis, 
                intent, products, session_action
            )
            
            # STEP 6: Create MessageAnalysis object
            analysis = MessageAnalysis(
                message_id=message_id,
                intent=intent,
                extracted_products=products,
                customer_notes=None,
                delivery_date=None,
                processing_time_ms=0  # Will set at end
            )
            
            # Add session information to analysis
            if session_result:
                analysis.session_id = session_result.get('session_id')
                analysis.session_status = session_result.get('status')
                analysis.requires_review = session_result.get('requires_review', False)
            
            # STEP 7: Handle session completion (create final order)
            if (session_result and 
                session_result.get('status') == 'CLOSED' and 
                session_result.get('order_created')):
                logger.info(f"✅ Created consolidated order from session for message {message_id}")
            
            # STEP 8: Update message with AI analysis and session data
            analysis.processing_time_ms = int((time.time() - start_time) * 1000)
            
            await update_message_ai_data(
                self.database, message_id, analysis, self.distributor_id
            )
            
            logger.info(
                f"✅ Completed session-aware processing for message {message_id} "
                f"(intent: {intent.intent}, session: {analysis.session_id}, "
                f"products: {len(products)}, time: {analysis.processing_time_ms}ms)"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to process message {message_id} with session awareness: {e}")
            return None
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            closed_count = self.session_manager.close_expired_sessions()
            if closed_count > 0:
                logger.info(f"Closed {closed_count} expired sessions")
        except Exception as e:
            logger.warning(f"Failed to cleanup expired sessions: {e}")
    
    async def _get_session_context(self, conversation_id: str, active_session) -> str:
        """
        Get context including active session information.
        
        Args:
            conversation_id: The conversation ID
            active_session: Active session if any
            
        Returns:
            Context string for AI analysis
        """
        context_parts = []
        
        try:
            # Get recent messages (last 10)
            recent_messages = await get_recent_messages_for_context(
                self.database, conversation_id, self.distributor_id, limit=10
            )
            if recent_messages:
                context_parts.append("Recent messages:")
                for msg in recent_messages[-5:]:
                    content = msg.get('content', '')[:100]
                    context_parts.append(f"- {content}")
            
            # Add active session context
            if active_session:
                session_items = self.session_manager.get_session_items(active_session.id)
                if session_items:
                    context_parts.append(f"\nActive order session (started {active_session.started_at}):")
                    context_parts.append(f"Status: {active_session.status.value}")
                    context_parts.append("Current items:")
                    for item in session_items[:5]:  # Show first 5 items
                        context_parts.append(f"- {item.quantity} {item.product_unit} {item.product_name}")
                    
                    if len(session_items) > 5:
                        context_parts.append(f"... and {len(session_items) - 5} more items")
        
        except Exception as e:
            logger.warning(f"Failed to get session context: {e}")
        
        return "\n".join(context_parts) if context_parts else "No previous context"
    
    async def _analyze_with_ai(
        self, content: str, context: str
    ) -> Optional[Tuple[MessageIntent, List[ExtractedProduct], str]]:
        """
        Analyze message with AI for session-aware processing.
        
        Returns:
            Tuple of (intent, products, session_action) if successful, None otherwise
        """
        try:
            # Get product catalog context
            catalog_context = ""
            try:
                catalog = await fetch_product_catalog(self.database, self.distributor_id)
                if catalog:
                    product_names = [p.product_name for p in catalog[:10]]
                    catalog_context = f"\n\nAVAILABLE PRODUCTS (sample): {', '.join(product_names)}"
            except:
                pass
            
            prompt = f"""
            Analyze this customer message in the context of an ongoing conversation and return a JSON response:
            
            MESSAGE: "{content}"
            
            CONTEXT: {context}{catalog_context}
            
            Return ONLY valid JSON in this exact format:
            {{
              "intent": "BUY",
              "confidence": 0.85,
              "reasoning": "Customer expressing purchase intent",
              "session_action": "START_OR_CONTINUE",
              "products": [
                {{
                  "name": "aceite de canola",
                  "quantity": 1,
                  "unit": "litro",
                  "original_text": "un litro de aceite de canola",
                  "confidence": 0.8
                }}
              ]
            }}
            
            Remember:
            - Consider the conversation context when determining intent
            - If there's an active session, this might be adding to it or modifying it
            - Look for closing signals like "eso es todo", "gracias", "confirma"
            - For modifications, use intent "MODIFY" and session_action "MODIFY_EXISTING"
            - For confirmations, use intent "CONFIRM" and session_action "CLOSE_SESSION"
            """
            
            result = await session_aware_agent.run(prompt, deps=self.deps)
            response_text = str(result.data)
            
            # Parse JSON response
            try:
                import json
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    data = json.loads(json_str)
                    
                    # Create intent from JSON
                    intent = MessageIntent(
                        intent=data.get('intent', 'OTHER'),
                        confidence=float(data.get('confidence', 0.5)),
                        reasoning=data.get('reasoning', 'AI analysis')
                    )
                    
                    # Create products from JSON
                    products = []
                    if data.get('products'):
                        for p in data['products']:
                            products.append(ExtractedProduct(
                                product_name=p.get('name', ''),
                                quantity=int(p.get('quantity', 1)),
                                unit=p.get('unit'),
                                original_text=p.get('original_text', content),
                                confidence=float(p.get('confidence', intent.confidence))
                            ))
                    
                    session_action = data.get('session_action', 'NO_ACTION')
                    
                    return intent, products, session_action
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                return None
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None
    
    async def _manage_session(
        self,
        message_data: Dict[str, Any],
        active_session,
        pattern_analysis: Dict[str, Any],
        intent: MessageIntent,
        products: List[ExtractedProduct],
        session_action: str
    ) -> Optional[Dict[str, Any]]:
        """
        Manage order session based on analysis results.
        
        Args:
            message_data: Original message data
            active_session: Current active session if any
            pattern_analysis: Pattern detection results
            intent: AI-determined intent
            products: Extracted products
            session_action: AI-suggested session action
            
        Returns:
            Dictionary with session results
        """
        message_id = message_data.get('id', '')
        conversation_id = message_data.get('conversation_id', '')
        
        try:
            # Determine final action based on pattern analysis and AI
            should_start_session = (
                not active_session and
                (intent.intent in ['BUY', 'MODIFY'] or
                 pattern_analysis['suggested_action'] == 'START_OR_EXTEND_SESSION' or
                 session_action == 'START_OR_CONTINUE') and
                pattern_analysis['overall_confidence'] >= 0.5
            )
            
            should_close_session = (
                active_session and
                (intent.intent == 'CONFIRM' or
                 pattern_analysis['suggested_action'] == 'CLOSE_SESSION' or
                 session_action == 'CLOSE_SESSION') and
                pattern_analysis.get('closing_confidence', 0) >= 0.6
            )
            
            should_extend_session = (
                active_session and
                (intent.intent in ['BUY', 'MODIFY'] or
                 pattern_analysis['suggested_action'] == 'START_OR_EXTEND_SESSION' or
                 session_action in ['START_OR_CONTINUE', 'MODIFY_EXISTING']) and
                not should_close_session
            )
            
            # Execute session actions
            if should_start_session:
                return await self._start_new_session(message_data, products, pattern_analysis)
            
            elif should_extend_session:
                return await self._extend_existing_session(active_session, message_data, products, intent)
            
            elif should_close_session:
                return await self._close_session(active_session, message_data)
            
            else:
                # No session action needed
                logger.info(f"No session action needed for message {message_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to manage session for message {message_id}: {e}")
            return None
    
    async def _start_new_session(
        self,
        message_data: Dict[str, Any],
        products: List[ExtractedProduct],
        pattern_analysis: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Start a new order session."""
        message_id = message_data.get('id', '')
        conversation_id = message_data.get('conversation_id', '')
        
        try:
            # Create new session
            session = self.session_manager.create_session(
                conversation_id=conversation_id,
                distributor_id=self.distributor_id,
                initial_message_id=message_id,
                metadata={
                    'started_by_message': message_id,
                    'pattern_confidence': pattern_analysis['overall_confidence'],
                    'extracted_items_count': len(pattern_analysis.get('extracted_items', []))
                }
            )
            
            if not session:
                logger.error(f"Failed to create session for message {message_id}")
                return None
            
            # Add products to session
            items_added = 0
            for product in products:
                item_id = self.session_manager.add_session_item(
                    session_id=session.id,
                    product_name=product.product_name,
                    quantity=product.quantity,
                    source_message_id=message_id,
                    original_text=product.original_text,
                    product_unit=product.unit or "units",
                    ai_confidence=product.confidence
                )
                if item_id:
                    items_added += 1
            
            # Also add items from pattern analysis
            for item in pattern_analysis.get('extracted_items', []):
                if not any(p.product_name.lower() == item['product_name'].lower() for p in products):
                    item_id = self.session_manager.add_session_item(
                        session_id=session.id,
                        product_name=item['product_name'],
                        quantity=item['quantity'],
                        source_message_id=message_id,
                        original_text=item['original_text'],
                        product_unit=item['unit'],
                        ai_confidence=item['confidence']
                    )
                    if item_id:
                        items_added += 1
            
            # Transition to COLLECTING if we have items
            if items_added > 0:
                self.session_manager.transition_status(
                    session.id,
                    SessionStatus.COLLECTING,
                    event_data={'items_added': items_added}
                )
            
            logger.info(f"✅ Started new session {session.id} with {items_added} items")
            
            return {
                'session_id': session.id,
                'status': 'COLLECTING',
                'items_added': items_added,
                'requires_review': False
            }
            
        except Exception as e:
            logger.error(f"Failed to start new session: {e}")
            return None
    
    async def _extend_existing_session(
        self,
        active_session,
        message_data: Dict[str, Any],
        products: List[ExtractedProduct],
        intent: MessageIntent
    ) -> Optional[Dict[str, Any]]:
        """Extend an existing order session."""
        message_id = message_data.get('id', '')
        
        try:
            # Add message to session
            added = self.session_manager.add_message_to_session(
                active_session.id,
                message_id,
                extend_session=True
            )
            
            if not added:
                logger.error(f"Failed to add message {message_id} to session {active_session.id}")
                return None
            
            # Add new products to session
            items_added = 0
            items_modified = 0
            
            for product in products:
                if intent.intent == 'MODIFY':
                    # Handle modifications (simplified - could be more sophisticated)
                    # For now, just add as new items with modification flag
                    item_id = self.session_manager.add_session_item(
                        session_id=active_session.id,
                        product_name=f"[MODIFIED] {product.product_name}",
                        quantity=product.quantity,
                        source_message_id=message_id,
                        original_text=product.original_text,
                        product_unit=product.unit or "units",
                        ai_confidence=product.confidence
                    )
                    if item_id:
                        items_modified += 1
                else:
                    # Add new items
                    item_id = self.session_manager.add_session_item(
                        session_id=active_session.id,
                        product_name=product.product_name,
                        quantity=product.quantity,
                        source_message_id=message_id,
                        original_text=product.original_text,
                        product_unit=product.unit or "units",
                        ai_confidence=product.confidence
                    )
                    if item_id:
                        items_added += 1
            
            logger.info(f"✅ Extended session {active_session.id} (+{items_added} items, ~{items_modified} modified)")
            
            return {
                'session_id': active_session.id,
                'status': active_session.status.value,
                'items_added': items_added,
                'items_modified': items_modified,
                'requires_review': items_modified > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to extend session: {e}")
            return None
    
    async def _close_session(
        self,
        active_session,
        message_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Close an active session and create the final order."""
        message_id = message_data.get('id', '')
        
        try:
            # Add the closing message to session
            self.session_manager.add_message_to_session(
                active_session.id,
                message_id,
                extend_session=False
            )
            
            # Transition to REVIEWING status
            self.session_manager.transition_status(
                active_session.id,
                SessionStatus.REVIEWING,
                event_data={'closed_by_message': message_id}
            )
            
            # Consolidate session into order
            order_request = self.session_manager.consolidate_session(active_session.id)
            
            if not order_request:
                logger.error(f"Failed to consolidate session {active_session.id}")
                # Close session anyway
                self.session_manager.transition_status(
                    active_session.id,
                    SessionStatus.CLOSED,
                    event_data={'error': 'consolidation_failed'}
                )
                return {
                    'session_id': active_session.id,
                    'status': 'CLOSED',
                    'order_created': False,
                    'error': 'consolidation_failed'
                }
            
            # Create the actual order
            order_creation = OrderCreation(
                customer_id=order_request.customer_id,
                distributor_id=order_request.distributor_id,
                conversation_id=order_request.conversation_id,
                channel=order_request.channel,
                products=order_request.products,
                delivery_date=order_request.delivery_date,
                additional_comment=order_request.additional_comment,
                ai_confidence=order_request.ai_confidence,
                source_message_ids=active_session.collected_message_ids,
                is_consolidated=True,
                order_session_id=active_session.id
            )
            
            order_id = await create_order(self.database, order_creation)
            
            if order_id:
                # Mark session as closed successfully
                self.session_manager.transition_status(
                    active_session.id,
                    SessionStatus.CLOSED,
                    event_data={
                        'order_created': True,
                        'order_id': order_id,
                        'closed_by_message': message_id
                    }
                )
                
                logger.info(f"✅ Closed session {active_session.id} and created order {order_id}")
                
                return {
                    'session_id': active_session.id,
                    'status': 'CLOSED',
                    'order_created': True,
                    'order_id': order_id,
                    'requires_review': order_request.requires_review
                }
            else:
                # Failed to create order
                self.session_manager.transition_status(
                    active_session.id,
                    SessionStatus.CLOSED,
                    event_data={'error': 'order_creation_failed'}
                )
                
                return {
                    'session_id': active_session.id,
                    'status': 'CLOSED',
                    'order_created': False,
                    'error': 'order_creation_failed'
                }
            
        except Exception as e:
            logger.error(f"Failed to close session: {e}")
            return None


def create_session_aware_order_processor(
    database: DatabaseService, distributor_id: str
) -> SessionAwareOrderProcessor:
    """
    Factory function for session-aware order processor.
    
    Args:
        database: Database service instance
        distributor_id: The distributor ID
        
    Returns:
        SessionAwareOrderProcessor instance
    """
    return SessionAwareOrderProcessor(database, distributor_id)