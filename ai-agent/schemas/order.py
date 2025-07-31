"""
Order management schemas for the Order Agent system.

Defines Pydantic models for order creation, order products, and order lifecycle management.
Mirrors the database structure from order_products table.
"""

from __future__ import annotations as _annotations

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime, date
from decimal import Decimal


class OrderProduct(BaseModel):
    """
    Individual product line item within an order.
    
    Maps to the order_products table structure with AI metadata fields.
    """
    
    product_name: str = Field(
        ...,
        min_length=1,
        description="Product name as extracted from customer message"
    )
    
    quantity: int = Field(
        ...,
        ge=1,
        description="Quantity ordered"
    )
    
    unit: Optional[str] = Field(
        None,
        description="Unit of measurement (bottles, cases, kg, etc.)"
    )
    
    unit_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Price per unit in distributor's currency"
    )
    
    line_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Total price for this line item (quantity × unit_price)"
    )
    
    ai_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence score for this product extraction"
    )
    
    original_text: str = Field(
        ...,
        min_length=1,
        description="Original message text that mentioned this product"
    )
    
    matched_product_id: Optional[str] = Field(
        None,
        description="ID of matched product from catalog"
    )
    
    matching_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score for product catalog matching"
    )
    
    @validator('product_name')
    def validate_product_name(cls, v):
        """Clean and validate product name."""
        return v.strip()
    
    @validator('unit')
    def validate_unit(cls, v):
        """Clean unit if provided."""
        if v:
            return v.strip().lower()
        return v
    
    @validator('line_price')
    def validate_line_price(cls, v, values):
        """Calculate line price if not provided."""
        if v is None and 'unit_price' in values and 'quantity' in values:
            unit_price = values.get('unit_price')
            quantity = values.get('quantity')
            if unit_price is not None and quantity is not None:
                return Decimal(str(unit_price)) * quantity
        return v
    
    @property
    def is_matched_to_catalog(self) -> bool:
        """Check if product is matched to catalog."""
        return self.matched_product_id is not None
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if extraction is high confidence."""
        return self.ai_confidence > 0.8


class OrderCreation(BaseModel):
    """
    Complete order creation model.
    
    Contains all information needed to create an order in the database
    with proper multi-tenant and AI metadata.
    """
    
    customer_id: str = Field(
        ...,
        min_length=1,
        description="UUID of the customer placing the order"
    )
    
    distributor_id: str = Field(
        ...,
        min_length=1,
        description="UUID of the distributor processing the order"
    )
    
    conversation_id: Optional[str] = Field(
        None,
        description="ID of the conversation where this order originated"
    )
    
    channel: Literal["WHATSAPP", "SMS", "EMAIL"] = Field(
        ...,
        description="Communication channel where order was received"
    )
    
    products: List[OrderProduct] = Field(
        ...,
        min_length=1,
        description="List of products in the order"
    )
    
    delivery_date: Optional[str] = Field(
        None,
        description="Requested delivery date (ISO format or customer text)"
    )
    
    additional_comment: Optional[str] = Field(
        None,
        description="Additional notes or special instructions"
    )
    
    ai_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall AI confidence for the entire order"
    )
    
    source_message_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of message IDs that contributed to this order"
    )
    
    @validator('additional_comment')
    def validate_additional_comment(cls, v):
        """Clean additional comment if provided."""
        if v:
            return v.strip()
        return v
    
    @validator('ai_confidence')
    def validate_overall_confidence(cls, v, values):
        """Ensure overall confidence is not higher than individual product confidences."""
        if 'products' in values:
            products = values['products']
            if products:
                max_product_confidence = max(p.ai_confidence for p in products)
                if v > max_product_confidence:
                    return max_product_confidence
        return v
    
    @property
    def total_items(self) -> int:
        """Get total number of items across all products."""
        return sum(product.quantity for product in self.products)
    
    @property
    def total_amount(self) -> Optional[Decimal]:
        """Calculate total order amount if prices are available."""
        total = Decimal('0')
        has_prices = False
        
        for product in self.products:
            if product.line_price is not None:
                total += product.line_price
                has_prices = True
            elif product.unit_price is not None:
                total += Decimal(str(product.unit_price)) * product.quantity
                has_prices = True
        
        return total if has_prices else None
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if the entire order is high confidence."""
        return self.ai_confidence > 0.8
    
    @property
    def requires_review(self) -> bool:
        """Check if order requires human review."""
        # Require review if overall confidence is low
        if self.ai_confidence < 0.8:
            return True
        
        # Require review if any product has low confidence
        if any(not product.is_high_confidence for product in self.products):
            return True
        
        # Require review if no products are matched to catalog
        if not any(product.is_matched_to_catalog for product in self.products):
            return True
        
        return False


class OrderDatabaseInsert(BaseModel):
    """
    Order database insert model.
    
    Maps directly to the orders table structure for database insertion.
    """
    
    customer_id: str
    distributor_id: str
    conversation_id: Optional[str] = None
    channel: str
    status: str = Field(default="PENDING", description="Order status")
    received_date: str = Field(default_factory=lambda: date.today().isoformat())
    received_time: str = Field(default_factory=lambda: datetime.now().time().isoformat())
    delivery_date: Optional[str] = None
    total_amount: Decimal = Field(default=Decimal('0.00'), description="Total order amount")
    additional_comment: Optional[str] = None
    ai_generated: bool = Field(default=True)
    ai_confidence: float
    ai_source_message_id: Optional[str] = None
    requires_review: bool = Field(default=True)
    
    @classmethod
    def from_order_creation(
        cls, 
        order: OrderCreation, 
        total_amount: Optional[Decimal] = None
    ) -> 'OrderDatabaseInsert':
        """
        Create database insert model from OrderCreation.
        
        Args:
            order: Complete order creation model
            total_amount: Calculated total amount
            
        Returns:
            OrderDatabaseInsert: Database insert model
        """
        # Ensure total_amount is never None - use provided value, order's total, or default to 0
        final_total = total_amount or order.total_amount or Decimal('0.00')
        
        return cls(
            customer_id=order.customer_id,
            distributor_id=order.distributor_id,
            conversation_id=order.conversation_id,
            channel=order.channel,
            delivery_date=order.delivery_date,
            total_amount=final_total,
            additional_comment=order.additional_comment,
            ai_confidence=order.ai_confidence,
            ai_source_message_id=order.source_message_ids[0] if order.source_message_ids else None,
            requires_review=order.requires_review
        )


class OrderProductDatabaseInsert(BaseModel):
    """
    Order product database insert model.
    
    Maps directly to the order_products table structure for database insertion.
    """
    
    order_id: str
    product_name: str
    quantity: int
    product_unit: str = Field(default="", description="Unit of measurement - column is required in DB")
    unit_price: Decimal = Field(default=Decimal('0.00'), description="Price per unit - NOT NULL constraint in DB")
    line_price: Decimal = Field(default=Decimal('0.00'), description="Total line price - NOT NULL constraint in DB")
    ai_extracted: bool = Field(default=True)
    ai_confidence: float
    ai_original_text: str
    matched_product_id: Optional[str] = None
    matching_confidence: Optional[float] = None
    line_order: int = Field(default=1, description="Position of this line in the order")
    
    @classmethod
    def from_order_product(
        cls, 
        product: OrderProduct, 
        order_id: str, 
        line_order: int = 1
    ) -> 'OrderProductDatabaseInsert':
        """
        Create database insert model from OrderProduct.
        
        Args:
            product: Order product model
            order_id: ID of the parent order
            line_order: Position of this line in the order
            
        Returns:
            OrderProductDatabaseInsert: Database insert model
        """
        # Ensure prices are never None due to NOT NULL constraints
        unit_price = product.unit_price or Decimal('0.00')
        line_price = product.line_price or Decimal('0.00')
        
        return cls(
            order_id=order_id,
            product_name=product.product_name,
            quantity=product.quantity,
            product_unit=product.unit or "",  # Map unit to product_unit, use empty string if None
            unit_price=unit_price,
            line_price=line_price,
            ai_confidence=product.ai_confidence,
            ai_original_text=product.original_text,
            matched_product_id=product.matched_product_id,
            matching_confidence=product.matching_confidence,
            line_order=line_order
        )