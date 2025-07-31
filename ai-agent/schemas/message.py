"""
Message processing schemas for the Order Agent system.

Defines Pydantic models for message analysis, intent classification, and product extraction.
"""

from __future__ import annotations as _annotations

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime


class MessageIntent(BaseModel):
    """
    Message intent classification with confidence scoring.
    
    Represents the AI's analysis of what the customer wants to accomplish
    with their message.
    """
    
    intent: Literal["BUY", "QUESTION", "COMPLAINT", "FOLLOW_UP", "OTHER"] = Field(
        ..., 
        description="The classified intent of the customer's message"
    )
    
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="AI confidence score for the intent classification (0.0-1.0)"
    )
    
    reasoning: str = Field(
        ..., 
        min_length=10,
        description="Explanation of why this intent was chosen by the AI"
    )
    
    @validator('reasoning')
    def validate_reasoning(cls, v):
        """Ensure reasoning is meaningful."""
        if len(v.strip()) < 10:
            raise ValueError('Reasoning must be at least 10 characters long')
        return v.strip()


class ExtractedProduct(BaseModel):
    """
    Product information extracted from customer message.
    
    Represents individual products mentioned by the customer, with AI confidence
    and original text for traceability. Includes status tracking for the
    hybrid validation workflow.
    """
    
    product_name: str = Field(
        ..., 
        min_length=1,
        description="Product name as mentioned by the customer"
    )
    
    quantity: int = Field(
        ..., 
        ge=1, 
        description="Quantity requested by the customer"
    )
    
    unit: Optional[str] = Field(
        None, 
        description="Unit of measurement mentioned (bottles, cases, kg, etc.)"
    )
    
    original_text: str = Field(
        ..., 
        min_length=1,
        description="Original text fragment that mentioned this product"
    )
    
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="AI confidence score for this product extraction (0.0-1.0)"
    )
    
    # Hybrid workflow status tracking
    status: Literal["draft", "pending", "confirmed", "rejected"] = Field(
        default="draft",
        description="Validation status in the hybrid workflow"
    )
    
    matched_product_id: Optional[str] = Field(
        None,
        description="ID of matched catalog product after validation"
    )
    
    matched_product_name: Optional[str] = Field(
        None,
        description="Official name of matched catalog product"
    )
    
    validation_notes: Optional[str] = Field(
        None,
        description="Notes from the validation process"
    )
    
    clarification_asked: Optional[str] = Field(
        None,
        description="Clarifying question asked to customer if any"
    )
    
    @validator('product_name')
    def validate_product_name(cls, v):
        """Clean and validate product name."""
        return v.strip().lower()
    
    @validator('unit')
    def validate_unit(cls, v):
        """Clean and validate unit if provided."""
        if v:
            return v.strip().lower()
        return v
    
    @validator('original_text')
    def validate_original_text(cls, v):
        """Ensure original text is preserved."""
        return v.strip()


class MessageAnalysis(BaseModel):
    """
    Complete analysis result for a customer message.
    
    Contains all AI-extracted information from a message including intent,
    products, and metadata for processing.
    """
    
    message_id: str = Field(
        ..., 
        min_length=1,
        description="Unique identifier of the analyzed message"
    )
    
    intent: MessageIntent = Field(
        ...,
        description="Classified intent of the message"
    )
    
    extracted_products: List[ExtractedProduct] = Field(
        default_factory=list,
        description="List of products extracted from the message"
    )
    
    customer_notes: Optional[str] = Field(
        None,
        description="Additional notes or special instructions from the customer"
    )
    
    delivery_date: Optional[str] = Field(
        None,
        description="Requested delivery date if mentioned (ISO format)"
    )
    
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Time taken to process this message in milliseconds"
    )
    
    requires_clarification: bool = Field(
        default=False,
        description="Whether this message requires clarification from the customer"
    )
    
    suggested_question: Optional[str] = Field(
        None,
        description="Suggested clarifying question to send to the customer"
    )
    
    @validator('customer_notes')
    def validate_customer_notes(cls, v):
        """Clean customer notes if provided."""
        if v:
            return v.strip()
        return v
    
    @validator('delivery_date')
    def validate_delivery_date(cls, v):
        """Validate delivery date format if provided."""
        if v:
            try:
                # Try to parse as ISO date
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                # If not ISO format, return as-is (customer's original text)
                return v
        return v
    
    @validator('suggested_question')
    def validate_suggested_question(cls, v):
        """Clean suggested question if provided."""
        if v:
            return v.strip()
        return v
    
    @property
    def has_order_intent(self) -> bool:
        """Check if this message has ordering intent."""
        return self.intent.intent == "BUY"
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if the analysis is high confidence (>0.8)."""
        return self.intent.confidence > 0.8
    
    @property
    def product_count(self) -> int:
        """Get the number of extracted products."""
        return len(self.extracted_products)


class MessageUpdate(BaseModel):
    """
    Update model for updating message AI analysis in database.
    
    Used to update the messages table with AI-extracted data.
    """
    
    ai_processed: bool = Field(default=True, description="Mark message as AI processed")
    
    ai_confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Overall AI confidence for the message analysis"
    )
    
    ai_extracted_intent: str = Field(
        ...,
        description="AI-extracted intent as string for database storage"
    )
    
    ai_extracted_products: Optional[List[dict]] = Field(
        None,
        description="AI-extracted products as JSON for database storage"
    )
    
    ai_processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds"
    )
    
    @classmethod
    def from_analysis(cls, analysis: MessageAnalysis) -> 'MessageUpdate':
        """
        Create MessageUpdate from MessageAnalysis.
        
        Args:
            analysis: Complete message analysis
            
        Returns:
            MessageUpdate: Database update model
        """
        # Convert ExtractedProduct objects to dict for JSON storage
        products_json = None
        if analysis.extracted_products:
            products_json = [product.dict() for product in analysis.extracted_products]
        
        return cls(
            ai_confidence=analysis.intent.confidence,
            ai_extracted_intent=analysis.intent.intent,
            ai_extracted_products=products_json,
            ai_processing_time_ms=analysis.processing_time_ms
        )