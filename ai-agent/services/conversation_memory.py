"""
Enhanced conversation memory service for autonomous agents.

Manages customer preferences, conversation context, and successful
interaction patterns to improve future autonomous decisions.
"""

from __future__ import annotations as _annotations

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from services.database import DatabaseService
from schemas.autonomous_agent import (
    CustomerPreference, AutonomousAgentContext, LearningEvent
)
from tools.supabase_tools import (
    get_recent_messages_for_context, get_recent_orders, get_customer_info
)

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Enhanced memory service for autonomous agent context and learning.
    
    Manages customer preferences, conversation patterns, and successful
    interaction history to improve autonomous decision making.
    """
    
    def __init__(self, database: DatabaseService):
        """
        Initialize conversation memory service.
        
        Args:
            database: Database service instance
        """
        self.database = database
        self.preference_cache = {}  # In-memory cache for frequent lookups
        self.pattern_cache = {}     # Cache for successful patterns
        logger.info("Initialized ConversationMemory service")
    
    async def build_agent_context(
        self,
        message_data: Dict[str, Any],
        distributor_id: str,
        business_goals: List[Any]
    ) -> AutonomousAgentContext:
        """
        Build comprehensive context for autonomous agent decision making.
        
        Args:
            message_data: Current message being processed
            distributor_id: Distributor ID for multi-tenant isolation
            business_goals: Current business goals configuration
            
        Returns:
            AutonomousAgentContext: Rich context for decision making
        """
        try:
            customer_id = message_data.get('customer_id', '')
            conversation_id = message_data.get('conversation_id', '')
            
            logger.debug(f"Building agent context for customer {customer_id}")
            
            # Gather context components in parallel where possible
            customer_info = await self._get_customer_info(customer_id, distributor_id)
            customer_prefs = await self._get_customer_preferences(customer_id, distributor_id)
            conversation_history = await self._get_conversation_context(conversation_id, distributor_id)
            recent_orders = await self._get_recent_orders(customer_id, distributor_id)
            inventory_status = await self._get_inventory_context(distributor_id)
            time_context = await self._get_time_context()
            
            # Extract any previous AI analysis from message data
            extracted_intent = None
            extracted_products = []
            
            # Build the comprehensive context
            context = AutonomousAgentContext(
                customer_id=customer_id,
                customer_name=customer_info.get('name') if customer_info else None,
                customer_preferences=customer_prefs,
                conversation_id=conversation_id,
                conversation_history=conversation_history,
                current_message=message_data,
                distributor_id=distributor_id,
                business_goals=business_goals,
                inventory_status=inventory_status,
                time_context=time_context,
                extracted_intent=extracted_intent,
                extracted_products=extracted_products,
                recent_orders=recent_orders,
                order_session_context=None  # Could be populated later
            )
            
            logger.info(f"Built agent context: {len(customer_prefs)} preferences, "
                       f"{len(conversation_history)} messages, {len(recent_orders)} orders")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build agent context: {e}")
            # Return minimal context to prevent complete failure
            return AutonomousAgentContext(
                customer_id=message_data.get('customer_id', ''),
                conversation_id=message_data.get('conversation_id', ''),
                current_message=message_data,
                distributor_id=distributor_id,
                business_goals=business_goals,
                time_context=await self._get_time_context()
            )
    
    async def learn_customer_preference(
        self,
        customer_id: str,
        distributor_id: str,
        preference: CustomerPreference
    ) -> bool:
        """
        Learn and store a customer preference.
        
        Args:
            customer_id: Customer ID
            distributor_id: Distributor ID
            preference: Preference to learn
            
        Returns:
            bool: True if preference was stored successfully
        """
        try:
            # Store preference in database
            preference_data = {
                'customer_id': customer_id,
                'distributor_id': distributor_id,
                'preference_type': preference.preference_type,
                'preference_value': preference.value,
                'confidence': preference.confidence,
                'learned_from': preference.learned_from,
                'created_at': preference.created_at,
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if similar preference already exists
            existing = await self._find_similar_preference(
                customer_id, distributor_id, preference.preference_type
            )
            
            if existing:
                # Update existing preference with higher confidence
                if preference.confidence > existing.get('confidence', 0):
                    await self.database.update_single(
                        table='customer_preferences',
                        data={
                            'preference_value': preference.value,
                            'confidence': preference.confidence,
                            'learned_from': preference.learned_from,
                            'updated_at': datetime.now().isoformat()
                        },
                        filters={'id': existing['id']},
                        distributor_id=distributor_id
                    )
                    logger.info(f"Updated customer preference {preference.preference_type} for {customer_id}")
            else:
                # Create new preference
                await self.database.insert_single(
                    table='customer_preferences',
                    data=preference_data
                )
                logger.info(f"Learned new customer preference {preference.preference_type} for {customer_id}")
            
            # Update cache
            cache_key = f"{customer_id}:{distributor_id}"
            if cache_key in self.preference_cache:
                del self.preference_cache[cache_key]  # Invalidate cache
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn customer preference: {e}")
            return False
    
    async def record_learning_event(
        self,
        event: LearningEvent
    ) -> bool:
        """
        Record a learning event for future improvement.
        
        Args:
            event: Learning event to record
            
        Returns:
            bool: True if event was recorded successfully
        """
        try:
            event_data = {
                'event_type': event.event_type,
                'context_summary': event.context_summary,
                'action_taken': event.action_taken,
                'outcome': event.outcome,
                'expected_outcome': event.expected_outcome,
                'success_metrics': json.dumps(event.success_metrics),
                'lesson_learned': event.lesson_learned,
                'timestamp': event.timestamp,
                'customer_id': event.customer_id,
                'distributor_id': event.distributor_id
            }
            
            await self.database.insert_single(
                table='learning_events',
                data=event_data
            )
            
            logger.info(f"Recorded learning event: {event.event_type} for {event.customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record learning event: {e}")
            return False
    
    async def get_successful_patterns(
        self,
        distributor_id: str,
        pattern_type: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get successful interaction patterns for learning.
        
        Args:
            distributor_id: Distributor ID
            pattern_type: Type of pattern to retrieve (optional)
            limit: Maximum patterns to return
            
        Returns:
            List[Dict]: Successful patterns
        """
        try:
            cache_key = f"patterns:{distributor_id}:{pattern_type}"
            if cache_key in self.pattern_cache:
                return self.pattern_cache[cache_key]
            
            filters = {'distributor_id': distributor_id}
            if pattern_type:
                filters['event_type'] = pattern_type
            
            # Get successful events (positive outcomes)
            events = await self.database.execute_query(
                table='learning_events',
                operation='select',
                filters=filters,
                distributor_id=distributor_id
            )
            
            if events:
                # Filter for successful events and sort by success metrics
                successful_events = []
                for event in events:
                    try:
                        metrics = json.loads(event.get('success_metrics', '{}'))
                        # Consider event successful if it has positive metrics
                        if any(v > 0.7 for v in metrics.values() if isinstance(v, (int, float))):
                            successful_events.append(event)
                    except:
                        continue
                
                # Sort by timestamp (most recent first) and limit
                successful_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                result = successful_events[:limit]
                
                # Cache result
                self.pattern_cache[cache_key] = result
                
                logger.info(f"Found {len(result)} successful patterns for {distributor_id}")
                return result
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get successful patterns: {e}")
            return []
    
    async def _get_customer_info(
        self, customer_id: str, distributor_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get customer information."""
        try:
            return await get_customer_info(self.database, customer_id, distributor_id)
        except Exception as e:
            logger.warning(f"Failed to get customer info: {e}")
            return None
    
    async def _get_customer_preferences(
        self, customer_id: str, distributor_id: str
    ) -> List[CustomerPreference]:
        """Get customer preferences with caching."""
        try:
            cache_key = f"{customer_id}:{distributor_id}"
            if cache_key in self.preference_cache:
                return self.preference_cache[cache_key]
            
            # Query database for preferences
            prefs_data = await self.database.execute_query(
                table='customer_preferences',
                operation='select',
                filters={'customer_id': customer_id},
                distributor_id=distributor_id
            )
            
            preferences = []
            if prefs_data:
                for pref_data in prefs_data:
                    preference = CustomerPreference(
                        preference_type=pref_data['preference_type'],
                        value=pref_data['preference_value'],
                        confidence=pref_data['confidence'],
                        learned_from=pref_data['learned_from'],
                        created_at=pref_data.get('created_at')
                    )
                    preferences.append(preference)
            
            # Cache preferences
            self.preference_cache[cache_key] = preferences
            
            logger.debug(f"Loaded {len(preferences)} preferences for customer {customer_id}")
            return preferences
            
        except Exception as e:
            logger.warning(f"Failed to get customer preferences: {e}")
            return []
    
    async def _get_conversation_context(
        self, conversation_id: str, distributor_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history for context."""
        try:
            return await get_recent_messages_for_context(
                self.database, conversation_id, distributor_id, limit=10
            )
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {e}")
            return []
    
    async def _get_recent_orders(
        self, customer_id: str, distributor_id: str
    ) -> List[Dict[str, Any]]:
        """Get recent customer orders."""
        try:
            return await get_recent_orders(
                self.database, customer_id, distributor_id, hours=168  # 7 days
            )
        except Exception as e:
            logger.warning(f"Failed to get recent orders: {e}")
            return []
    
    async def _get_inventory_context(
        self, distributor_id: str
    ) -> List[Dict[str, Any]]:
        """Get inventory status for decision making."""
        try:
            # This would query product inventory
            # For now, return empty list - can be implemented later
            return []
        except Exception as e:
            logger.warning(f"Failed to get inventory context: {e}")
            return []
    
    async def _get_time_context(self) -> Dict[str, Any]:
        """Get temporal context for decision making."""
        try:
            now = datetime.now()
            
            # Simple business hours logic (9 AM - 6 PM weekdays)
            is_business_hours = (
                now.weekday() < 5 and  # Monday-Friday
                9 <= now.hour < 18     # 9 AM - 6 PM
            )
            
            # Peak hours logic (10 AM - 12 PM, 2 PM - 4 PM)
            is_peak_hours = (
                is_business_hours and
                ((10 <= now.hour < 12) or (14 <= now.hour < 16))
            )
            
            return {
                'current_time': now.isoformat(),
                'business_hours': is_business_hours,
                'day_of_week': now.strftime('%A'),
                'is_holiday': False,  # Could be enhanced with holiday detection
                'peak_hours': is_peak_hours
            }
        except Exception as e:
            logger.warning(f"Failed to get time context: {e}")
            # Return safe defaults
            return {
                'current_time': datetime.now().isoformat(),
                'business_hours': True,
                'day_of_week': 'Monday',
                'is_holiday': False,
                'peak_hours': False
            }
    
    async def _find_similar_preference(
        self, customer_id: str, distributor_id: str, preference_type: str
    ) -> Optional[Dict[str, Any]]:
        """Find existing similar preference."""
        try:
            prefs = await self.database.execute_query(
                table='customer_preferences',
                operation='select',
                filters={
                    'customer_id': customer_id,
                    'preference_type': preference_type
                },
                distributor_id=distributor_id
            )
            
            if prefs and len(prefs) > 0:
                # Return most recent preference
                prefs.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
                return prefs[0]
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to find similar preference: {e}")
            return None
    
    def clear_caches(self):
        """Clear all memory caches."""
        self.preference_cache.clear()
        self.pattern_cache.clear()
        logger.info("Cleared conversation memory caches")


def create_conversation_memory(database: DatabaseService) -> ConversationMemory:
    """
    Factory function to create conversation memory service.
    
    Args:
        database: Database service instance
        
    Returns:
        ConversationMemory: Configured memory service
    """
    return ConversationMemory(database)