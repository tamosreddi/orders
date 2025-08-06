"""
Order Session Manager for Multi-Message Order Processing

This module manages conversation order sessions using a state machine approach.
It handles the lifecycle of orders that span multiple messages within a conversation.

State Machine Flow:
ACTIVE → COLLECTING → REVIEWING → CLOSED

Author: AI Assistant
Date: 2025-08-04
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal

from .database import DatabaseService
from schemas.order import OrderProduct, OrderRequest
from supabase import create_client
from config.settings import settings


logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Order session status states."""
    ACTIVE = "ACTIVE"
    COLLECTING = "COLLECTING" 
    REVIEWING = "REVIEWING"
    CLOSED = "CLOSED"


class EventType(Enum):
    """Order session event types."""
    SESSION_STARTED = "SESSION_STARTED"
    MESSAGE_ADDED = "MESSAGE_ADDED"
    ITEM_EXTRACTED = "ITEM_EXTRACTED"
    ITEM_MODIFIED = "ITEM_MODIFIED"
    ITEM_CANCELLED = "ITEM_CANCELLED"
    STATUS_CHANGED = "STATUS_CHANGED"
    SESSION_EXTENDED = "SESSION_EXTENDED"
    AI_PROCESSED = "AI_PROCESSED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    SESSION_CLOSED = "SESSION_CLOSED"
    ORDER_CREATED = "ORDER_CREATED"


@dataclass
class OrderSessionItem:
    """Represents an item collected during an order session."""
    id: Optional[str]
    product_name: str
    quantity: Decimal
    product_unit: str = "units"
    unit_price: Optional[Decimal] = None
    line_total: Optional[Decimal] = None
    ai_confidence: float = 0.0
    source_message_id: Optional[str] = None
    original_text: Optional[str] = None
    suggested_product_id: Optional[str] = None
    matching_confidence: float = 0.0
    item_status: str = "ACTIVE"
    notes: Optional[str] = None


@dataclass
class OrderSession:
    """Represents a conversation order session."""
    id: Optional[str]
    conversation_id: str
    distributor_id: str
    status: SessionStatus
    started_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    closed_at: Optional[datetime] = None
    collected_message_ids: List[str] = None
    total_messages_count: int = 0
    consolidated_order_data: Optional[Dict] = None
    confidence_score: float = 0.0
    ai_processing_attempts: int = 0
    requires_review: bool = False
    session_metadata: Dict = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.collected_message_ids is None:
            self.collected_message_ids = []
        if self.session_metadata is None:
            self.session_metadata = {}


class OrderSessionManager:
    """
    Manages order sessions for multi-message order processing.
    
    This class handles the state machine lifecycle of order sessions,
    from detection of order intent through consolidation and finalization.
    """
    
    def __init__(self, database_service: DatabaseService):
        """Initialize the Order Session Manager."""
        self.database = database_service
        # Create synchronous supabase client for session operations
        self.supabase = create_client(settings.supabase_url, settings.supabase_key)
        self.default_session_timeout = timedelta(minutes=30)
        self.extension_timeout = timedelta(minutes=5)
        
    def get_active_session(self, conversation_id: str) -> Optional[OrderSession]:
        """
        Get the active order session for a conversation.
        
        Args:
            conversation_id: The conversation ID to check
            
        Returns:
            Active OrderSession if found, None otherwise
        """
        try:
            result = self.supabase.table("conversation_order_sessions")\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .in_("status", ["ACTIVE", "COLLECTING"])\
                .gt("expires_at", datetime.now().isoformat())\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                session_data = result.data[0]
                return self._dict_to_session(session_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting active session: {e}")
            return None
    
    def create_session(
        self, 
        conversation_id: str, 
        distributor_id: str,
        initial_message_id: str,
        metadata: Optional[Dict] = None
    ) -> Optional[OrderSession]:
        """
        Create a new order session.
        
        Args:
            conversation_id: The conversation ID
            distributor_id: The distributor ID
            initial_message_id: The message that triggered the session
            metadata: Optional session metadata
            
        Returns:
            Created OrderSession if successful, None otherwise
        """
        try:
            now = datetime.now()
            expires_at = now + self.default_session_timeout
            
            session_data = {
                "conversation_id": conversation_id,
                "distributor_id": distributor_id,
                "status": SessionStatus.ACTIVE.value,
                "started_at": now.isoformat(),
                "last_activity_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "collected_message_ids": [initial_message_id],
                "total_messages_count": 1,
                "session_metadata": metadata or {}
            }
            
            result = self.supabase.table("conversation_order_sessions")\
                .insert(session_data)\
                .execute()
            
            if result.data:
                session = self._dict_to_session(result.data[0])
                
                # Link the initial message to this session
                self._link_message_to_session(initial_message_id, session.id)
                
                # Log session creation event
                self._log_event(
                    session.id,
                    EventType.SESSION_STARTED,
                    message_id=initial_message_id,
                    event_data={"initial_message_id": initial_message_id}
                )
                
                logger.info(f"Created order session {session.id} for conversation {conversation_id}")
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating order session: {e}")
            return None
    
    def add_message_to_session(
        self, 
        session_id: str, 
        message_id: str,
        extend_session: bool = True
    ) -> bool:
        """
        Add a message to an existing order session.
        
        Args:
            session_id: The session ID
            message_id: The message ID to add
            extend_session: Whether to extend the session timeout
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current session data
            session = self.get_session_by_id(session_id)
            if not session:
                return False
            
            # Add message ID to the collected messages
            updated_message_ids = list(session.collected_message_ids)
            if message_id not in updated_message_ids:
                updated_message_ids.append(message_id)
            
            # Prepare update data
            update_data = {
                "collected_message_ids": updated_message_ids,
                "total_messages_count": len(updated_message_ids),
                "last_activity_at": datetime.now().isoformat()
            }
            
            # Extend session timeout if requested
            if extend_session:
                new_expires_at = datetime.now() + self.extension_timeout
                update_data["expires_at"] = new_expires_at.isoformat()
            
            # Update session
            result = self.supabase.table("conversation_order_sessions")\
                .update(update_data)\
                .eq("id", session_id)\
                .execute()
            
            if result.data:
                # Link message to session
                self._link_message_to_session(message_id, session_id)
                
                # Log event
                self._log_event(
                    session_id,
                    EventType.MESSAGE_ADDED,
                    message_id=message_id,
                    event_data={"total_messages": len(updated_message_ids)}
                )
                
                logger.info(f"Added message {message_id} to session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding message to session: {e}")
            return False
    
    def transition_status(
        self, 
        session_id: str, 
        new_status: SessionStatus,
        user_id: Optional[str] = None,
        event_data: Optional[Dict] = None
    ) -> bool:
        """
        Transition a session to a new status.
        
        Args:
            session_id: The session ID
            new_status: The new status to transition to
            user_id: Optional user ID if human-initiated
            event_data: Optional event data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "status": new_status.value,
                "updated_at": datetime.now().isoformat()
            }
            
            # If closing the session, set closed_at
            if new_status == SessionStatus.CLOSED:
                update_data["closed_at"] = datetime.now().isoformat()
            
            result = self.supabase.table("conversation_order_sessions")\
                .update(update_data)\
                .eq("id", session_id)\
                .execute()
            
            if result.data:
                # Log status change event
                self._log_event(
                    session_id,
                    EventType.STATUS_CHANGED,
                    user_id=user_id,
                    event_data=event_data or {},
                    new_status=new_status.value
                )
                
                logger.info(f"Session {session_id} transitioned to {new_status.value}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error transitioning session status: {e}")
            return False
    
    def add_session_item(
        self,
        session_id: str,
        product_name: str,
        quantity: Decimal,
        source_message_id: str,
        original_text: str,
        product_unit: str = "units",
        ai_confidence: float = 0.0,
        suggested_product_id: Optional[str] = None,
        matching_confidence: float = 0.0
    ) -> Optional[str]:
        """
        Add an item to an order session.
        
        Args:
            session_id: The session ID
            product_name: Name of the product
            quantity: Quantity ordered
            source_message_id: Message where this item was mentioned
            original_text: Original text that mentioned this item
            product_unit: Unit of measurement
            ai_confidence: AI confidence in extraction
            suggested_product_id: Suggested product from catalog
            matching_confidence: Confidence in product matching
            
        Returns:
            Item ID if successful, None otherwise
        """
        try:
            item_data = {
                "session_id": session_id,
                "product_name": product_name,
                "quantity": float(quantity),
                "product_unit": product_unit,
                "source_message_id": source_message_id,
                "original_text": original_text,
                "ai_confidence": ai_confidence,
                "suggested_product_id": suggested_product_id,
                "matching_confidence": matching_confidence,
                "item_status": "ACTIVE"
            }
            
            result = self.supabase.table("order_session_items")\
                .insert(item_data)\
                .execute()
            
            if result.data:
                item_id = result.data[0]["id"]
                
                # Log item extraction event
                self._log_event(
                    session_id,
                    EventType.ITEM_EXTRACTED,
                    message_id=source_message_id,
                    event_data={
                        "item_id": item_id,
                        "product_name": product_name,
                        "quantity": float(quantity)
                    }
                )
                
                logger.info(f"Added item {item_id} to session {session_id}")
                return item_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error adding session item: {e}")
            return None
    
    def get_session_items(self, session_id: str) -> List[OrderSessionItem]:
        """
        Get all items for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of OrderSessionItem objects
        """
        try:
            result = self.supabase.table("order_session_items")\
                .select("*")\
                .eq("session_id", session_id)\
                .eq("item_status", "ACTIVE")\
                .order("sequence_number")\
                .execute()
            
            items = []
            for item_data in result.data:
                item = OrderSessionItem(
                    id=item_data["id"],
                    product_name=item_data["product_name"],
                    quantity=Decimal(str(item_data["quantity"])),
                    product_unit=item_data["product_unit"],
                    unit_price=Decimal(str(item_data["unit_price"])) if item_data["unit_price"] else None,
                    line_total=Decimal(str(item_data["line_total"])) if item_data["line_total"] else None,
                    ai_confidence=item_data["ai_confidence"],
                    source_message_id=item_data["source_message_id"],
                    original_text=item_data["original_text"],
                    suggested_product_id=item_data["suggested_product_id"],
                    matching_confidence=item_data["matching_confidence"],
                    item_status=item_data["item_status"],
                    notes=item_data["notes"]
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting session items: {e}")
            return []
    
    def consolidate_session(self, session_id: str) -> Optional[OrderRequest]:
        """
        Consolidate all session items into a final order.
        
        Args:
            session_id: The session ID to consolidate
            
        Returns:
            OrderRequest object if successful, None otherwise
        """
        try:
            session = self.get_session_by_id(session_id)
            items = self.get_session_items(session_id)
            
            if not session or not items:
                return None
            
            # Get conversation details
            conversation = self._get_conversation(session.conversation_id)
            if not conversation:
                return None
            
            # Create order products list
            order_products = []
            total_amount = Decimal('0.00')
            
            for item in items:
                order_product = OrderProduct(
                    product_name=item.product_name,
                    quantity=item.quantity,
                    product_unit=item.product_unit,
                    unit_price=item.unit_price or Decimal('0.00'),
                    line_price=item.line_total or (item.quantity * (item.unit_price or Decimal('0.00'))),
                    ai_extracted=True,
                    ai_confidence=item.ai_confidence,
                    ai_original_text=item.original_text,
                    suggested_product_id=item.suggested_product_id,
                    matching_confidence=item.matching_confidence
                )
                order_products.append(order_product)
                total_amount += order_product.line_price
            
            # Create consolidated order
            order_request = OrderRequest(
                customer_id=conversation["customer_id"],
                distributor_id=session.distributor_id,
                conversation_id=session.conversation_id,
                channel="WHATSAPP",  # Default, should be dynamic
                status="REVIEW",
                total_amount=total_amount,
                ai_generated=True,
                ai_confidence=session.confidence_score,
                ai_source_message_id=session.collected_message_ids[0] if session.collected_message_ids else None,
                requires_review=session.requires_review,
                additional_comment=f"Consolidated from {len(items)} items across {session.total_messages_count} messages",
                products=order_products
            )
            
            # Store consolidated data in session
            consolidated_data = {
                "order_request": order_request.dict(),
                "consolidated_at": datetime.now().isoformat(),
                "total_items": len(items),
                "total_messages": session.total_messages_count
            }
            
            self.supabase.table("conversation_order_sessions")\
                .update({
                    "consolidated_order_data": consolidated_data,
                    "confidence_score": session.confidence_score
                })\
                .eq("id", session_id)\
                .execute()
            
            # Log consolidation event
            self._log_event(
                session_id,
                EventType.AI_PROCESSED,
                event_data={
                    "consolidated_items": len(items),
                    "total_amount": float(total_amount),
                    "confidence_score": session.confidence_score
                },
                ai_triggered=True,
                ai_confidence=session.confidence_score
            )
            
            logger.info(f"Consolidated session {session_id} into order with {len(items)} items")
            return order_request
            
        except Exception as e:
            logger.error(f"Error consolidating session: {e}")
            return None
    
    def close_expired_sessions(self) -> int:
        """
        Close all expired sessions.
        
        Returns:
            Number of sessions closed
        """
        try:
            # Use the helper function from database migration
            result = self.supabase.rpc("close_timed_out_sessions").execute()
            sessions_closed = result.data if result.data else 0
            
            logger.info(f"Closed {sessions_closed} expired sessions")
            return sessions_closed
            
        except Exception as e:
            logger.error(f"Error closing expired sessions: {e}")
            return 0
    
    def get_session_by_id(self, session_id: str) -> Optional[OrderSession]:
        """
        Get a session by its ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            OrderSession if found, None otherwise
        """
        try:
            result = self.supabase.table("conversation_order_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .single()\
                .execute()
            
            if result.data:
                return self._dict_to_session(result.data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session by ID: {e}")
            return None
    
    def _dict_to_session(self, data: Dict) -> OrderSession:
        """Convert database dict to OrderSession object."""
        return OrderSession(
            id=data["id"],
            conversation_id=data["conversation_id"],
            distributor_id=data["distributor_id"],
            status=SessionStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"].replace('Z', '+00:00')),
            last_activity_at=datetime.fromisoformat(data["last_activity_at"].replace('Z', '+00:00')),
            expires_at=datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00')),
            closed_at=datetime.fromisoformat(data["closed_at"].replace('Z', '+00:00')) if data["closed_at"] else None,
            collected_message_ids=data["collected_message_ids"] or [],
            total_messages_count=data["total_messages_count"] or 0,
            consolidated_order_data=data["consolidated_order_data"],
            confidence_score=float(data["confidence_score"] or 0.0),
            ai_processing_attempts=data["ai_processing_attempts"] or 0,
            requires_review=data["requires_review"] or False,
            session_metadata=data["session_metadata"] or {}
        )
    
    def _link_message_to_session(self, message_id: str, session_id: str) -> bool:
        """Link a message to an order session."""
        try:
            result = self.supabase.table("messages")\
                .update({"order_session_id": session_id})\
                .eq("id", message_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error linking message to session: {e}")
            return False
    
    def _get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation details."""
        try:
            result = self.supabase.table("conversations")\
                .select("*")\
                .eq("id", conversation_id)\
                .single()\
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None
    
    def _log_event(
        self,
        session_id: str,
        event_type: EventType,
        message_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_data: Optional[Dict] = None,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        ai_triggered: bool = False,
        ai_confidence: Optional[float] = None
    ) -> bool:
        """Log an event for audit trail."""
        try:
            event_record = {
                "session_id": session_id,
                "event_type": event_type.value,
                "message_id": message_id,
                "user_id": user_id,
                "event_data": event_data or {},
                "previous_status": previous_status,
                "new_status": new_status,
                "ai_triggered": ai_triggered,
                "ai_confidence": ai_confidence
            }
            
            result = self.supabase.table("order_session_events")\
                .insert(event_record)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error logging session event: {e}")
            return False