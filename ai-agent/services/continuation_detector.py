"""
Continuation Detector for Multi-Message Order Processing

This service detects when customer messages should be treated as continuations
of existing PENDING orders rather than new orders. Uses a hybrid approach:
1. Fast rule-based detection for obvious patterns
2. AI enhancement for uncertain cases

Author: AI Assistant
Date: 2025-08-07
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from services.database import DatabaseService
from tools.supabase_tools import get_recent_orders
from schemas.message import ExtractedProduct

logger = logging.getLogger(__name__)


@dataclass
class ContinuationResult:
    """Result of continuation detection analysis."""
    
    is_continuation: bool
    confidence: float
    target_order_id: Optional[str] = None
    target_order_number: Optional[str] = None
    reasoning: str = ""
    detection_method: str = ""  # RULES, AI, HYBRID
    recent_order_context: Optional[Dict] = None


class ContinuationDetector:
    """
    Detects when messages should continue existing PENDING orders.
    
    Uses hybrid detection:
    1. Rule-based detection for explicit continuation phrases
    2. AI enhancement for uncertain or implicit cases
    3. Order status boundaries (PENDING vs ACCEPTED/REJECTED)
    """
    
    # Explicit continuation phrases in Spanish
    CONTINUATION_PHRASES = [
        # Direct continuation
        "también", "tambien", "además", "ademas", 
        "y también", "y tambien", "y además", "y ademas",
        
        # Addition patterns
        "ah y", "ah también", "ah tambien", "ah y también",
        "y dame", "y deme", "y ponme", "y pon",
        
        # More patterns
        "también quiero", "tambien quiero", "además quiero", "ademas quiero",
        "y quiero", "ah quiero", "ah y quiero",
        
        # Implicit additions
        "dame también", "dame tambien", "ponme también", "ponme tambien",
        "de esos también", "de esos tambien"
    ]
    
    # Time window for considering continuation (minutes)
    CONTINUATION_TIME_WINDOW_MINUTES = 10
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.60
    
    def __init__(self):
        """Initialize the continuation detector."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def check_continuation(
        self, 
        message_content: str,
        conversation_id: str,
        customer_id: str,
        database: DatabaseService,
        distributor_id: str,
        extracted_products: List[ExtractedProduct] = None
    ) -> ContinuationResult:
        """
        Check if a message should be treated as a continuation of an existing order.
        
        Args:
            message_content: The customer's message
            conversation_id: Conversation ID
            customer_id: Customer ID
            database: Database service
            distributor_id: Distributor ID
            extracted_products: Products extracted from message
            
        Returns:
            ContinuationResult with detection results
        """
        try:
            # Step 1: Get recent PENDING orders
            recent_orders = await self._get_recent_pending_orders(
                customer_id, database, distributor_id
            )
            
            if not recent_orders:
                return ContinuationResult(
                    is_continuation=False,
                    confidence=1.0,
                    reasoning="No recent PENDING orders found",
                    detection_method="RULES"
                )
            
            # Step 2: Rule-based detection (fast and free)
            rule_result = self._detect_continuation_rules(
                message_content, recent_orders
            )
            
            # Step 3: If rules are confident, return result
            if rule_result.confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                return rule_result
            
            # Step 4: If we have products but rules are uncertain, 
            # this could be AI-enhanced continuation detection
            # For now, implement rule-based only and prepare for AI enhancement
            
            return rule_result
            
        except Exception as e:
            self.logger.error(f"Error checking continuation: {e}")
            return ContinuationResult(
                is_continuation=False,
                confidence=0.0,
                reasoning=f"Detection error: {e}",
                detection_method="ERROR"
            )
    
    async def _get_recent_pending_orders(
        self, 
        customer_id: str, 
        database: DatabaseService, 
        distributor_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get recent PENDING orders for the customer.
        
        Args:
            customer_id: Customer ID
            database: Database service
            distributor_id: Distributor ID
            
        Returns:
            List of recent PENDING orders
        """
        try:
            # Get orders from last 10 minutes
            hours_back = self.CONTINUATION_TIME_WINDOW_MINUTES / 60.0
            
            recent_orders = await get_recent_orders(
                database, customer_id, distributor_id, hours=hours_back
            )
            
            # Filter for PENDING status only
            pending_orders = [
                order for order in recent_orders 
                if order.get('status') == 'PENDING'
            ]
            
            self.logger.info(f"Found {len(pending_orders)} recent PENDING orders for customer {customer_id}")
            return pending_orders
            
        except Exception as e:
            self.logger.error(f"Error getting recent pending orders: {e}")
            return []
    
    def _detect_continuation_rules(
        self, 
        message_content: str, 
        recent_orders: List[Dict[str, Any]]
    ) -> ContinuationResult:
        """
        Apply rule-based continuation detection.
        
        Args:
            message_content: Customer message
            recent_orders: List of recent PENDING orders
            
        Returns:
            ContinuationResult from rule-based analysis
        """
        message_lower = message_content.lower().strip()
        
        # Check for explicit continuation phrases
        found_phrases = []
        for phrase in self.CONTINUATION_PHRASES:
            if phrase.lower() in message_lower:
                found_phrases.append(phrase)
        
        if found_phrases:
            # High confidence - explicit continuation detected
            target_order = recent_orders[0]  # Most recent order
            
            return ContinuationResult(
                is_continuation=True,
                confidence=0.95,
                target_order_id=target_order.get('id'),
                target_order_number=target_order.get('order_number'),
                reasoning=f"Explicit continuation phrases found: {', '.join(found_phrases)}",
                detection_method="RULES",
                recent_order_context={
                    'order_id': target_order.get('id'),
                    'order_number': target_order.get('order_number'),
                    'created_at': target_order.get('created_at'),
                    'product_count': len(target_order.get('products', []))
                }
            )
        
        # Check for implicit continuation patterns
        implicit_patterns = [
            r'\by\s+\w+',  # "y algo" patterns
            r'\bah\s+\w+',  # "ah algo" patterns  
            r'\bponme\s+\w+',  # "ponme algo" patterns
            r'\bdame\s+\w+',  # "dame algo" patterns
        ]
        
        implicit_matches = []
        for pattern in implicit_patterns:
            if re.search(pattern, message_lower):
                implicit_matches.append(pattern)
        
        if implicit_matches:
            # Medium confidence - implicit patterns
            target_order = recent_orders[0]
            
            return ContinuationResult(
                is_continuation=True,
                confidence=0.70,
                target_order_id=target_order.get('id'),
                target_order_number=target_order.get('order_number'),
                reasoning=f"Implicit continuation patterns detected: {len(implicit_matches)} matches",
                detection_method="RULES",
                recent_order_context={
                    'order_id': target_order.get('id'),
                    'order_number': target_order.get('order_number'),
                    'created_at': target_order.get('created_at'),
                    'product_count': len(target_order.get('products', []))
                }
            )
        
        # Check for temporal-based continuation (recent order + new product order)
        if recent_orders:
            most_recent_order = recent_orders[0]
            try:
                order_time_str = most_recent_order.get('created_at', '')
                if 'T' in order_time_str:
                    order_time = datetime.fromisoformat(order_time_str.replace('Z', '+00:00'))
                else:
                    order_time = datetime.fromisoformat(f"{order_time_str}T00:00:00+00:00")
                
                current_time = datetime.now(timezone.utc)
                time_diff = current_time - order_time
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Could not parse order time: {order_time_str}, error: {e}")
                time_diff = timedelta(hours=24)  # Default to outside window
            
            # If order was created within continuation window
            if time_diff.total_seconds() / 60 <= self.CONTINUATION_TIME_WINDOW_MINUTES:
                # Check if message looks like a product order (not greeting/question)
                product_indicators = [
                    r'\d+\s+\w+',  # Numbers + product (e.g., "2 pepsis", "43 panes")
                    r'\w+\s+\d+',  # Product + numbers (e.g., "pepsi 2")
                    r'quiero\s+\w+', r'dame\s+\w+', r'ponme\s+\w+',  # Want/give/put patterns
                    r'necesito\s+\w+', r'mandame\s+\w+',  # Need/send patterns
                ]
                
                has_product_pattern = any(re.search(pattern, message_lower) for pattern in product_indicators)
                
                # Check for explicit rejection phrases that would break continuation
                rejection_phrases = [
                    "no", "nada más", "ya está", "eso es todo", "gracias",
                    "nuevo pedido", "otra orden", "cancelar", "cancel"
                ]
                has_rejection = any(phrase in message_lower for phrase in rejection_phrases)
                
                if has_product_pattern and not has_rejection:
                    return ContinuationResult(
                        is_continuation=True,
                        confidence=0.75,  # Medium-high confidence for temporal continuation
                        target_order_id=most_recent_order.get('id'),
                        target_order_number=most_recent_order.get('order_number'),
                        reasoning=f"Temporal continuation: product order within {time_diff.total_seconds()/60:.1f} minutes of recent order",
                        detection_method="TEMPORAL_RULES",
                        recent_order_context={
                            'order_id': most_recent_order.get('id'),
                            'order_number': most_recent_order.get('order_number'),
                            'created_at': most_recent_order.get('created_at'),
                            'time_diff_minutes': time_diff.total_seconds() / 60
                        }
                    )
        
        # No continuation detected
        return ContinuationResult(
            is_continuation=False,
            confidence=0.90,
            reasoning="No continuation phrases, patterns, or temporal context detected",
            detection_method="RULES"
        )
    
    def should_create_new_order(
        self, 
        recent_orders: List[Dict[str, Any]], 
        time_threshold_minutes: int = None
    ) -> bool:
        """
        Determine if a new order should be created based on order status and timing.
        
        Args:
            recent_orders: List of recent orders
            time_threshold_minutes: Time threshold for considering orders recent
            
        Returns:
            True if should create new order, False if can continue existing
        """
        if not recent_orders:
            return True  # No recent orders, create new
        
        threshold_minutes = time_threshold_minutes or self.CONTINUATION_TIME_WINDOW_MINUTES
        threshold_time = datetime.now() - timedelta(minutes=threshold_minutes)
        
        for order in recent_orders:
            order_time = datetime.fromisoformat(
                order['created_at'].replace('Z', '+00:00').replace('+00:00', '')
            )
            
            # If order is recent and PENDING, we can potentially continue it
            if (order_time >= threshold_time and 
                order.get('status') == 'PENDING'):
                return False  # Don't create new, can continue existing
        
        return True  # All recent orders are old or not PENDING
    
    def get_continuation_context_for_ai(
        self, 
        recent_orders: List[Dict[str, Any]]
    ) -> str:
        """
        Generate context string for AI continuation detection.
        
        Args:
            recent_orders: List of recent orders
            
        Returns:
            Context string for AI prompt
        """
        if not recent_orders:
            return "No recent orders"
        
        context_parts = []
        for i, order in enumerate(recent_orders[:2]):  # Top 2 recent orders
            products = order.get('products', [])
            product_names = [p.get('product_name', 'Unknown') for p in products]
            
            context_parts.append(
                f"Recent Order {i+1}: #{order.get('order_number', 'N/A')} "
                f"({order.get('status', 'Unknown')} status) "
                f"with {len(products)} items: {', '.join(product_names[:3])}"
                f"{'...' if len(products) > 3 else ''}"
            )
        
        return "\n".join(context_parts)