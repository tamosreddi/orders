"""
Autonomous Order Creator Service using exact same mechanism as order_agent.py.

This service creates orders from validated and consolidated products using the
identical order creation workflow as the existing StreamlinedOrderProcessor.

Key Features:
- Exact same mechanism as order_agent.py _create_simple_order()
- Handles consolidated session products
- Maintains compatibility with existing database schema
- Supports human validation flags and notes
"""

from __future__ import annotations as _annotations

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from services.database import DatabaseService
from schemas.message import ExtractedProduct
from schemas.order import OrderCreation, OrderProduct
from tools.supabase_tools import create_order
from services.enhanced_product_validator import ValidationResult, ValidationFlag

logger = logging.getLogger(__name__)


@dataclass
class OrderCreationResult:
    """Result of autonomous order creation."""
    success: bool
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    created_products_count: int = 0
    pending_products_count: int = 0
    human_validation_notes: List[str] = None
    
    def __post_init__(self):
        if self.human_validation_notes is None:
            self.human_validation_notes = []


class AutonomousOrderCreator:
    """
    Creates orders using the exact same mechanism as order_agent.py.
    
    This service follows the identical pattern from StreamlinedOrderProcessor._create_simple_order()
    to ensure consistency between autonomous and manual processing workflows.
    """
    
    def __init__(self, database: DatabaseService, distributor_id: str):
        self.database = database
        self.distributor_id = distributor_id
        logger.info(f"Initialized AutonomousOrderCreator for distributor {distributor_id}")
    
    async def create_autonomous_order(
        self,
        customer_id: str,
        conversation_id: str,
        validated_products: List[ExtractedProduct],
        validation_result: ValidationResult,
        source_message_ids: List[str],
        channel: str = "WHATSAPP",
        additional_notes: Optional[str] = None
    ) -> OrderCreationResult:
        """
        Create order from validated products using exact same mechanism as order_agent.py.
        
        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID  
            validated_products: Products that have been validated
            validation_result: Result from enhanced validation
            source_message_ids: List of message IDs that contributed to this order
            channel: Communication channel (default: WHATSAPP)
            additional_notes: Additional notes for the order
            
        Returns:
            OrderCreationResult with success status and details
        """
        logger.info(f"🚀 Creating autonomous order for customer {customer_id} with {len(validated_products)} products")
        
        try:
            # STEP 1: Filter for confirmed products only (same as order_agent.py line 869)
            confirmed_products = [p for p in validated_products if p.status == "confirmed"]
            pending_products = [p for p in validated_products if p.status == "pending"]
            
            logger.info(f"Products status: {len(confirmed_products)} confirmed, {len(pending_products)} pending")
            
            if not confirmed_products:
                logger.info("No confirmed products to create order - all products need human validation")
                return OrderCreationResult(
                    success=False,
                    error_message="No confirmed products available for order creation",
                    pending_products_count=len(pending_products),
                    human_validation_notes=self._extract_validation_notes(pending_products)
                )
            
            # STEP 2: Convert ExtractedProduct to OrderProduct (same as order_agent.py line 877)
            order_products = []
            for extracted in confirmed_products:
                order_product = OrderProduct(
                    product_name=extracted.matched_product_name or extracted.product_name,
                    quantity=extracted.quantity,
                    unit=extracted.unit,
                    unit_price=None,  # Pricing handled elsewhere (same as order_agent.py)
                    line_price=None,
                    ai_confidence=extracted.confidence,
                    original_text=extracted.original_text,
                    matched_product_id=extracted.matched_product_id,
                    matching_confidence=extracted.confidence
                )
                order_products.append(order_product)
            
            # STEP 3: Generate order comment with validation info
            order_comment = self._generate_order_comment(
                additional_notes, validation_result, confirmed_products, pending_products
            )
            
            # STEP 4: Create order (same as order_agent.py line 892)
            order_creation = OrderCreation(
                customer_id=customer_id,
                distributor_id=self.distributor_id,
                conversation_id=conversation_id,
                channel=channel,
                products=order_products,
                delivery_date=None,
                additional_comment=order_comment,
                ai_confidence=validation_result.confidence_score,
                source_message_ids=source_message_ids
            )
            
            # STEP 5: Call create_order (same as order_agent.py line 904)
            order_id = await create_order(self.database, order_creation)
            
            if order_id:
                logger.info(f"✅ Successfully created autonomous order {order_id} with {len(order_products)} products")
                
                return OrderCreationResult(
                    success=True,
                    order_id=order_id,
                    created_products_count=len(confirmed_products),
                    pending_products_count=len(pending_products),
                    human_validation_notes=self._extract_validation_notes(pending_products)
                )
            else:
                logger.error("Order creation returned None - database operation failed")
                return OrderCreationResult(
                    success=False,
                    error_message="Database order creation failed",
                    pending_products_count=len(pending_products),
                    human_validation_notes=self._extract_validation_notes(pending_products)
                )
            
        except Exception as e:
            logger.error(f"Failed to create autonomous order: {e}")
            return OrderCreationResult(
                success=False,
                error_message=f"Order creation error: {str(e)}",
                pending_products_count=len(validated_products),
                human_validation_notes=[f"Error occurred during order creation: {str(e)}"]
            )
    
    async def create_partial_order_with_flags(
        self,
        customer_id: str,
        conversation_id: str,
        validated_products: List[ExtractedProduct],
        validation_result: ValidationResult,
        source_message_ids: List[str],
        channel: str = "WHATSAPP"
    ) -> OrderCreationResult:
        """
        Create partial order from confirmed products while flagging pending ones for human review.
        
        This method creates an order with confirmed products immediately, while adding
        detailed notes about products that need human validation.
        """
        logger.info(f"🚀 Creating partial order with human validation flags")
        
        confirmed_products = [p for p in validated_products if p.status == "confirmed"] 
        pending_products = [p for p in validated_products if p.status == "pending"]
        
        if not confirmed_products:
            # No confirmed products - create a "review order" with all products pending
            return await self._create_review_order(
                customer_id, conversation_id, validated_products, validation_result, source_message_ids, channel
            )
        
        # Create order with confirmed products + human validation notes
        additional_notes = self._generate_human_validation_notes(validation_result, pending_products)
        
        return await self.create_autonomous_order(
            customer_id=customer_id,
            conversation_id=conversation_id,
            validated_products=confirmed_products,  # Only confirmed products
            validation_result=validation_result,
            source_message_ids=source_message_ids,
            channel=channel,
            additional_notes=additional_notes
        )
    
    async def _create_review_order(
        self,
        customer_id: str,
        conversation_id: str,
        validated_products: List[ExtractedProduct],
        validation_result: ValidationResult,
        source_message_ids: List[str],
        channel: str
    ) -> OrderCreationResult:
        """Create a review-only order when no products can be confirmed."""
        
        logger.info("Creating review order - no confirmed products available")
        
        try:
            # Convert all products to OrderProduct with zero pricing (needs human review)
            order_products = []
            for extracted in validated_products:
                order_product = OrderProduct(
                    product_name=extracted.matched_product_name or extracted.product_name,
                    quantity=extracted.quantity,
                    unit=extracted.unit or "units",
                    unit_price=0.0,  # Zero pricing - needs human review
                    line_price=0.0,
                    ai_confidence=extracted.confidence,
                    original_text=extracted.original_text,
                    matched_product_id=extracted.matched_product_id,
                    matching_confidence=extracted.confidence or 0.0
                )
                order_products.append(order_product)
            
            # Create order with REVIEW status and detailed notes
            order_comment = f"""
🤖 AUTONOMOUS AGENT - HUMAN VALIDATION REQUESTED

{validation_result.validation_summary}

PRODUCTS REQUIRING VALIDATION:
{self._format_pending_products_for_review(validated_products)}

VALIDATION FLAGS: {', '.join([flag.value for flag in validation_result.human_validation_flags])}

AI CONFIDENCE: {validation_result.confidence_score:.0%}
SOURCE MESSAGES: {len(source_message_ids)} messages
            """.strip()
            
            order_creation = OrderCreation(
                customer_id=customer_id,
                distributor_id=self.distributor_id,
                conversation_id=conversation_id,
                channel=channel,
                products=order_products,
                delivery_date=None,
                additional_comment=order_comment,
                ai_confidence=validation_result.confidence_score,
                source_message_ids=source_message_ids
            )
            
            order_id = await create_order(self.database, order_creation)
            
            if order_id:
                logger.info(f"✅ Created review order {order_id} - all {len(order_products)} products need human validation")
                
                return OrderCreationResult(
                    success=True,
                    order_id=order_id,
                    created_products_count=0,  # No confirmed products
                    pending_products_count=len(validated_products),
                    human_validation_notes=self._extract_validation_notes(validated_products)
                )
            else:
                return OrderCreationResult(
                    success=False,
                    error_message="Failed to create review order",
                    pending_products_count=len(validated_products)
                )
                
        except Exception as e:
            logger.error(f"Failed to create review order: {e}")
            return OrderCreationResult(
                success=False,
                error_message=f"Review order creation failed: {str(e)}",
                pending_products_count=len(validated_products)
            )
    
    def _generate_order_comment(
        self,
        additional_notes: Optional[str],
        validation_result: ValidationResult,
        confirmed_products: List[ExtractedProduct],
        pending_products: List[ExtractedProduct]
    ) -> str:
        """Generate comprehensive order comment with validation information."""
        
        comment_parts = ["🤖 AUTONOMOUS AGENT ORDER"]
        
        # Add validation summary
        comment_parts.append(f"Validation: {validation_result.validation_summary}")
        
        # Add product counts
        comment_parts.append(
            f"Products: {len(confirmed_products)} confirmed"
            + (f", {len(pending_products)} pending human review" if pending_products else "")
        )
        
        # Add validation flags if any
        if validation_result.human_validation_flags:
            flags_str = ", ".join([flag.value for flag in validation_result.human_validation_flags])
            comment_parts.append(f"Flags: {flags_str}")
        
        # Add AI confidence
        comment_parts.append(f"AI Confidence: {validation_result.confidence_score:.0%}")
        
        # Add additional notes
        if additional_notes:
            comment_parts.append(f"Notes: {additional_notes}")
        
        # Add pending products details if any
        if pending_products:
            comment_parts.append("\nPENDING HUMAN VALIDATION:")
            for product in pending_products:
                comment_parts.append(
                    f"- {product.product_name} (qty: {product.quantity}) - {product.validation_notes or 'Needs review'}"
                )
        
        return "\n".join(comment_parts)
    
    def _generate_human_validation_notes(
        self, validation_result: ValidationResult, pending_products: List[ExtractedProduct]
    ) -> str:
        """Generate notes specifically for human validation requirements."""
        
        notes_parts = []
        
        if ValidationFlag.HUMAN_VALIDATION_REQUESTED in validation_result.human_validation_flags:
            notes_parts.append("⚠️  HUMAN VALIDATION REQUESTED")
        
        if pending_products:
            notes_parts.append(f"{len(pending_products)} products need human review:")
            for product in pending_products:
                notes_parts.append(f"• {product.product_name}: {product.validation_notes or 'Requires validation'}")
        
        if validation_result.suggested_questions:
            notes_parts.append("Suggested questions for customer:")
            for question in validation_result.suggested_questions:
                notes_parts.append(f"• {question}")
        
        return "\n".join(notes_parts)
    
    def _format_pending_products_for_review(self, products: List[ExtractedProduct]) -> str:
        """Format pending products for human review."""
        
        formatted_products = []
        for i, product in enumerate(products, 1):
            formatted_products.append(
                f"{i}. {product.product_name} (qty: {product.quantity}{product.unit or ''}) "
                f"- {product.validation_notes or 'Needs validation'}"
            )
        
        return "\n".join(formatted_products)
    
    def _extract_validation_notes(self, products: List[ExtractedProduct]) -> List[str]:
        """Extract validation notes from products for result summary."""
        
        notes = []
        for product in products:
            if product.validation_notes:
                notes.append(f"{product.product_name}: {product.validation_notes}")
            else:
                notes.append(f"{product.product_name}: Requires human validation")
        
        return notes


# Factory function for easy integration
def create_autonomous_order_creator(
    database: DatabaseService, distributor_id: str
) -> AutonomousOrderCreator:
    """Create autonomous order creator service."""
    return AutonomousOrderCreator(database, distributor_id)