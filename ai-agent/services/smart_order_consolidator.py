"""
Smart Order Consolidation Service for Message Timing Analysis.

This service implements intelligent timing-based analysis to determine if multiple 
messages from the same customer should be consolidated into a single order.

Key Features:
- Message timing pattern analysis
- Context similarity detection  
- Order completion confidence scoring
- Smart consolidation decisions based on timing, content, and customer behavior
"""

from __future__ import annotations as _annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from services.database import DatabaseService
from schemas.message import ExtractedProduct, MessageIntent
from tools.supabase_tools import get_recent_messages_for_context

logger = logging.getLogger(__name__)


class ConsolidationDecision(Enum):
    """Consolidation decision types."""
    CONSOLIDATE = "consolidate"       # Add to existing order session
    NEW_ORDER = "new_order"          # Create new separate order
    WAIT_MORE = "wait_more"          # Wait for more messages before deciding
    ORDER_COMPLETE = "order_complete" # Current session is complete, create order


@dataclass
class MessageTimingPattern:
    """Analysis of message timing patterns."""
    time_since_last_message: timedelta
    message_frequency: float  # messages per minute in recent window
    conversation_pace: str    # "rapid", "normal", "slow", "pause"
    is_continuation: bool     # appears to be continuing previous thought
    completion_signals: List[str]  # detected completion keywords/patterns


@dataclass
class ConsolidationAnalysis:
    """Result of consolidation analysis."""
    decision: ConsolidationDecision
    confidence: float  # 0.0 to 1.0
    reasoning: str
    wait_duration_minutes: Optional[int] = None
    timing_pattern: Optional[MessageTimingPattern] = None
    should_create_order: bool = False
    consolidation_score: float = 0.0


class SmartOrderConsolidator:
    """
    Intelligent service for consolidating messages into orders based on timing analysis.
    
    This service analyzes message timing patterns, customer behavior, and content
    similarity to make smart decisions about when to consolidate multiple messages
    into a single order vs creating separate orders.
    """
    
    def __init__(self, database: DatabaseService):
        self.database = database
        
        # Timing thresholds for analysis
        self.quick_followup_seconds = 30      # Very quick follow-up (continuing thought)
        self.normal_conversation_minutes = 3   # Normal conversation pace
        self.order_completion_minutes = 8      # Likely order completion pause
        self.session_timeout_minutes = 15      # Session expires
        
        # Completion signal keywords
        self.completion_keywords = [
            # Spanish completion signals
            "eso es todo", "es todo", "nada más", "ya está", "listo",
            "eso sería todo", "con eso", "suficiente", "gracias",
            "eso me queda bien", "está bien", "perfecto",
            
            # English completion signals  
            "that's all", "that's it", "done", "complete", "finished",
            "nothing else", "good", "perfect", "thanks"
        ]
        
        # Continuation signal keywords (suggests more coming)
        self.continuation_keywords = [
            # Spanish continuation signals
            "también", "además", "y", "otra cosa", "ah", "espera",
            "también quiero", "y también", "ah sí",
            
            # English continuation signals
            "also", "and", "plus", "wait", "oh", "another thing"
        ]
        
        logger.info("Initialized SmartOrderConsolidator with timing analysis")
    
    async def analyze_for_consolidation(
        self,
        message_data: Dict[str, Any],
        extracted_products: List[ExtractedProduct],
        intent: MessageIntent
    ) -> ConsolidationAnalysis:
        """
        Analyze if message should be consolidated with previous messages or treated separately.
        
        Args:
            message_data: Current message data
            extracted_products: Products extracted from current message
            intent: Message intent classification
            
        Returns:
            ConsolidationAnalysis with decision and reasoning
        """
        customer_id = message_data.get('customer_id', '')
        conversation_id = message_data.get('conversation_id', '')
        content = message_data.get('content', '').strip().lower()
        message_timestamp = datetime.fromisoformat(
            message_data.get('created_at', datetime.now().isoformat())
        )
        
        logger.info(f"🔍 Analyzing consolidation for message from customer {customer_id}")
        
        # Only consolidate ORDER_RELATED messages
        if intent.intent != "ORDER_RELATED":
            return ConsolidationAnalysis(
                decision=ConsolidationDecision.NEW_ORDER,
                confidence=0.9,
                reasoning="Non-order message, process separately",
                should_create_order=False
            )
        
        # Get recent messages for timing analysis
        recent_messages = await self._get_recent_order_messages(
            conversation_id, customer_id, hours=1
        )
        
        if not recent_messages:
            # First order-related message - start new session
            return ConsolidationAnalysis(
                decision=ConsolidationDecision.WAIT_MORE,
                confidence=0.8,
                reasoning="First order message, wait for potential follow-ups",
                wait_duration_minutes=5,
                should_create_order=False
            )
        
        # Analyze timing patterns
        timing_pattern = await self._analyze_timing_pattern(
            message_timestamp, recent_messages, content
        )
        
        # Make consolidation decision based on timing analysis
        return await self._make_consolidation_decision(
            timing_pattern, extracted_products, content, recent_messages
        )
    
    async def _get_recent_order_messages(
        self, conversation_id: str, customer_id: str, hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get recent ORDER_RELATED messages for timing analysis."""
        try:
            # Get recent messages from conversation
            messages = await get_recent_messages_for_context(
                self.database, conversation_id, "", limit=20
            )
            
            if not messages:
                return []
            
            # Filter for recent ORDER_RELATED messages within time window
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_order_messages = []
            for msg in messages:
                msg_time = datetime.fromisoformat(
                    msg.get('created_at', datetime.now().isoformat())
                )
                
                # Check if message is recent and has order intent
                if msg_time > cutoff_time:
                    # Check if message has ORDER_RELATED intent in ai_data
                    ai_data = msg.get('ai_data', {})
                    if isinstance(ai_data, dict):
                        intent = ai_data.get('intent', {})
                        if isinstance(intent, dict) and intent.get('intent') == 'ORDER_RELATED':
                            recent_order_messages.append(msg)
            
            # Sort by timestamp (oldest first)
            recent_order_messages.sort(
                key=lambda x: datetime.fromisoformat(x.get('created_at', datetime.now().isoformat()))
            )
            
            return recent_order_messages
            
        except Exception as e:
            logger.warning(f"Could not get recent messages: {e}")
            return []
    
    async def _analyze_timing_pattern(
        self,
        current_timestamp: datetime,
        recent_messages: List[Dict[str, Any]],
        current_content: str
    ) -> MessageTimingPattern:
        """Analyze timing patterns of recent messages."""
        
        if not recent_messages:
            return MessageTimingPattern(
                time_since_last_message=timedelta(hours=24),
                message_frequency=0.0,
                conversation_pace="new",
                is_continuation=False,
                completion_signals=[]
            )
        
        # Get last message timestamp
        last_message = recent_messages[-1]
        last_timestamp = datetime.fromisoformat(
            last_message.get('created_at', datetime.now().isoformat())
        )
        
        time_since_last = current_timestamp - last_timestamp
        
        # Calculate message frequency (messages per minute in last 10 minutes)
        recent_window = current_timestamp - timedelta(minutes=10)
        recent_count = sum(
            1 for msg in recent_messages
            if datetime.fromisoformat(msg.get('created_at', datetime.now().isoformat())) > recent_window
        )
        message_frequency = recent_count / 10.0  # per minute
        
        # Determine conversation pace
        if time_since_last.total_seconds() <= self.quick_followup_seconds:
            pace = "rapid"
        elif time_since_last.total_seconds() <= self.normal_conversation_minutes * 60:
            pace = "normal"
        elif time_since_last.total_seconds() <= self.order_completion_minutes * 60:
            pace = "slow"
        else:
            pace = "pause"
        
        # Check for continuation signals
        is_continuation = any(
            keyword in current_content for keyword in self.continuation_keywords
        )
        
        # Check for completion signals
        completion_signals = [
            keyword for keyword in self.completion_keywords
            if keyword in current_content
        ]
        
        return MessageTimingPattern(
            time_since_last_message=time_since_last,
            message_frequency=message_frequency,
            conversation_pace=pace,
            is_continuation=is_continuation,
            completion_signals=completion_signals
        )
    
    async def _make_consolidation_decision(
        self,
        timing_pattern: MessageTimingPattern,
        extracted_products: List[ExtractedProduct],
        content: str,
        recent_messages: List[Dict[str, Any]]
    ) -> ConsolidationAnalysis:
        """Make the final consolidation decision based on analysis."""
        
        # Initialize decision variables
        decision = ConsolidationDecision.NEW_ORDER
        confidence = 0.5
        reasoning = "Default decision"
        should_create_order = False
        consolidation_score = 0.0
        wait_minutes = None
        
        # Decision logic based on timing patterns
        
        # CASE 1: Very quick follow-up (< 30 seconds)
        if timing_pattern.conversation_pace == "rapid":
            decision = ConsolidationDecision.CONSOLIDATE
            confidence = 0.95
            reasoning = "Very quick follow-up suggests continuation of same order"
            consolidation_score = 0.9
            
        # CASE 2: Explicit completion signals detected
        elif timing_pattern.completion_signals:
            completion_signal = timing_pattern.completion_signals[0]
            decision = ConsolidationDecision.ORDER_COMPLETE
            confidence = 0.9
            reasoning = f"Completion signal detected: '{completion_signal}'"
            should_create_order = True
            consolidation_score = 0.95
            
        # CASE 3: Continuation signals detected
        elif timing_pattern.is_continuation:
            decision = ConsolidationDecision.CONSOLIDATE  
            confidence = 0.85
            reasoning = "Continuation signal suggests adding to existing order"
            consolidation_score = 0.8
            
        # CASE 4: Normal conversation pace (1-3 minutes)
        elif timing_pattern.conversation_pace == "normal":
            if extracted_products:
                decision = ConsolidationDecision.CONSOLIDATE
                confidence = 0.75
                reasoning = "Normal pace with products, likely continuing order"
                consolidation_score = 0.7
            else:
                decision = ConsolidationDecision.WAIT_MORE
                confidence = 0.6
                reasoning = "Normal pace, wait to see if more products mentioned"
                wait_minutes = 3
                
        # CASE 5: Slow conversation pace (3-8 minutes)
        elif timing_pattern.conversation_pace == "slow":
            if len(recent_messages) >= 2:
                # Multiple messages already - likely order completion
                decision = ConsolidationDecision.ORDER_COMPLETE
                confidence = 0.8
                reasoning = "Slow pace after multiple messages suggests order completion"
                should_create_order = True
                consolidation_score = 0.8
            else:
                # First follow-up after delay - consolidate
                decision = ConsolidationDecision.CONSOLIDATE
                confidence = 0.65
                reasoning = "Slow pace but likely related to previous order"
                consolidation_score = 0.6
                
        # CASE 6: Long pause (> 8 minutes)
        elif timing_pattern.conversation_pace == "pause":
            if recent_messages:
                decision = ConsolidationDecision.ORDER_COMPLETE
                confidence = 0.9
                reasoning = "Long pause suggests previous order is complete"
                should_create_order = True
                consolidation_score = 0.9
            else:
                decision = ConsolidationDecision.NEW_ORDER
                confidence = 0.8
                reasoning = "Long pause, treat as new order"
        
        # CASE 7: High message frequency suggests active ordering
        if timing_pattern.message_frequency > 0.5:  # More than 1 message per 2 minutes
            if decision != ConsolidationDecision.ORDER_COMPLETE:
                # Boost consolidation confidence for active conversations
                if decision == ConsolidationDecision.NEW_ORDER:
                    decision = ConsolidationDecision.CONSOLIDATE
                confidence = min(confidence + 0.1, 1.0)
                consolidation_score = min(consolidation_score + 0.1, 1.0)
        
        logger.info(
            f"💡 Consolidation decision: {decision.value} "
            f"(confidence: {confidence:.2f}, "
            f"pace: {timing_pattern.conversation_pace}, "
            f"time_gap: {timing_pattern.time_since_last_message.total_seconds():.0f}s)"
        )
        
        return ConsolidationAnalysis(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            wait_duration_minutes=wait_minutes,
            timing_pattern=timing_pattern,
            should_create_order=should_create_order,
            consolidation_score=consolidation_score
        )
    
    def get_consolidation_stats(self) -> Dict[str, Any]:
        """Get statistics about consolidation decisions (for monitoring)."""
        # This would track decision patterns over time
        # For now, return basic info
        return {
            "service": "SmartOrderConsolidator",
            "timing_thresholds": {
                "quick_followup_seconds": self.quick_followup_seconds,
                "normal_conversation_minutes": self.normal_conversation_minutes,
                "order_completion_minutes": self.order_completion_minutes,
                "session_timeout_minutes": self.session_timeout_minutes
            },
            "keyword_counts": {
                "completion_keywords": len(self.completion_keywords),
                "continuation_keywords": len(self.continuation_keywords)
            }
        }


# Factory function for easy integration
def create_smart_order_consolidator(database: DatabaseService) -> SmartOrderConsolidator:
    """Create smart order consolidator service."""
    return SmartOrderConsolidator(database)