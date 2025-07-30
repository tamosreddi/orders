"""
Product matching schemas for the Order Agent system.

Defines Pydantic models for product catalog matching, fuzzy matching results,
and product validation logic.
"""

from __future__ import annotations as _annotations

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from decimal import Decimal


class ProductMatch(BaseModel):
    """
    Result of matching a customer product request to the catalog.
    
    Contains information about how well a customer's product mention
    matches a specific product in the distributor's catalog.
    """
    
    product_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the matched catalog product"
    )
    
    product_name: str = Field(
        ...,
        min_length=1,
        description="Official name of the matched catalog product"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score for this match (0.0-1.0)"
    )
    
    match_type: Literal["EXACT", "FUZZY", "ALIAS", "AI_ENHANCED"] = Field(
        ...,
        description="Type of matching algorithm that found this match"
    )
    
    match_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw matching score from the algorithm (0.0-1.0)"
    )
    
    # Additional product information for context
    sku: Optional[str] = Field(None, description="Product SKU code")
    unit: Optional[str] = Field(None, description="Product unit of sale")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Product unit price")
    category: Optional[str] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    
    # Matching metadata
    matched_aliases: List[str] = Field(
        default_factory=list,
        description="List of aliases that contributed to the match"
    )
    
    matched_keywords: List[str] = Field(
        default_factory=list,
        description="List of keywords that contributed to the match"
    )
    
    @validator('product_name')
    def validate_product_name(cls, v):
        """Clean product name."""
        return v.strip()
    
    @validator('match_score')
    def validate_match_score_consistency(cls, v, values):
        """Ensure match score is consistent with confidence."""
        if 'confidence' in values and 'match_type' in values:
            confidence = values['confidence']
            match_type = values['match_type']
            
            # For exact matches, scores should be very high
            if match_type == "EXACT" and v < 0.9:
                return 0.95  # Boost score for exact matches
            
            # Confidence should generally not exceed match score by much
            if confidence > v + 0.1:
                return confidence
        
        return v
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence match."""
        return self.confidence > 0.8
    
    @property
    def is_exact_match(self) -> bool:
        """Check if this is an exact match."""
        return self.match_type == "EXACT"
    
    @property
    def match_quality(self) -> str:
        """Get human-readable match quality."""
        if self.confidence >= 0.9:
            return "excellent"
        elif self.confidence >= 0.8:
            return "good"
        elif self.confidence >= 0.6:
            return "fair"
        else:
            return "poor"


class CatalogProduct(BaseModel):
    """
    Product from the distributor's catalog.
    
    Contains all information needed for matching customer requests
    to catalog products.
    """
    
    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Official product name")
    sku: Optional[str] = Field(None, description="Stock keeping unit code")
    description: Optional[str] = Field(None, description="Product description")
    category: Optional[str] = Field(None, description="Product category")
    unit: Optional[str] = Field(None, description="Unit of sale")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Price per unit")
    brand: Optional[str] = Field(None, description="Product brand")
    
    # AI matching fields
    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative names customers use for this product"
    )
    
    keywords: List[str] = Field(
        default_factory=list,
        description="Search keywords for AI matching"
    )
    
    ai_training_examples: List[str] = Field(
        default_factory=list,
        description="Example phrases customers use for this product"
    )
    
    common_misspellings: List[str] = Field(
        default_factory=list,
        description="Common misspellings the AI should recognize"
    )
    
    # Availability
    in_stock: bool = Field(default=True, description="Whether product is in stock")
    active: bool = Field(default=True, description="Whether product is actively sold")
    
    @property
    def search_terms(self) -> List[str]:
        """Get all searchable terms for this product."""
        terms = [self.name]
        
        if self.sku:
            terms.append(self.sku)
        
        terms.extend(self.aliases)
        terms.extend(self.keywords)
        terms.extend(self.ai_training_examples)
        terms.extend(self.common_misspellings)
        
        # Clean and deduplicate
        return list(set(term.strip().lower() for term in terms if term.strip()))
    
    @property
    def is_available(self) -> bool:
        """Check if product is available for ordering."""
        return self.active and self.in_stock


class ProductMatchingRequest(BaseModel):
    """
    Request for matching customer product mentions to catalog.
    
    Contains the customer's product request and context for matching.
    """
    
    customer_text: str = Field(
        ...,
        min_length=1,
        description="Customer's original text mentioning the product"
    )
    
    extracted_product_name: str = Field(
        ...,
        min_length=1,
        description="Product name as extracted by AI"
    )
    
    quantity: Optional[int] = Field(
        None,
        ge=1,
        description="Requested quantity (for context)"
    )
    
    unit: Optional[str] = Field(
        None,
        description="Requested unit (for context)"
    )
    
    customer_id: Optional[str] = Field(
        None,
        description="Customer ID for order history context"
    )
    
    distributor_id: str = Field(
        ...,
        description="Distributor ID for catalog filtering"
    )
    
    @validator('customer_text', 'extracted_product_name')
    def clean_text_fields(cls, v):
        """Clean text fields."""
        return v.strip()


class ProductMatchingResponse(BaseModel):
    """
    Response from product matching service.
    
    Contains all potential matches ranked by confidence.
    """
    
    request: ProductMatchingRequest = Field(
        ...,
        description="Original matching request"
    )
    
    matches: List[ProductMatch] = Field(
        default_factory=list,
        description="List of potential matches, ranked by confidence"
    )
    
    best_match: Optional[ProductMatch] = Field(
        None,
        description="Best match if any above threshold"
    )
    
    matching_time_ms: int = Field(
        ...,
        ge=0,
        description="Time taken to find matches in milliseconds"
    )
    
    total_products_searched: int = Field(
        ...,
        ge=0,
        description="Total number of catalog products searched"
    )
    
    @validator('best_match')
    def validate_best_match(cls, v, values):
        """Ensure best match is the highest confidence match."""
        if v is not None and 'matches' in values:
            matches = values['matches']
            if matches and matches[0].confidence != v.confidence:
                # Return the highest confidence match
                return matches[0]
        return v
    
    @property
    def has_high_confidence_match(self) -> bool:
        """Check if there's a high-confidence match."""
        return self.best_match is not None and self.best_match.is_high_confidence
    
    @property
    def match_count(self) -> int:
        """Get number of matches found."""
        return len(self.matches)
    
    @property
    def matching_succeeded(self) -> bool:
        """Check if matching found at least one viable match."""
        return self.best_match is not None and self.best_match.confidence > 0.5


class ProductValidationResult(BaseModel):
    """
    Result of validating extracted products against catalog.
    
    Contains validation status and any issues found.
    """
    
    product_name: str = Field(..., description="Product name being validated")
    
    is_valid: bool = Field(..., description="Whether product was successfully validated")
    
    match: Optional[ProductMatch] = Field(
        None,
        description="Best catalog match if found"
    )
    
    issues: List[str] = Field(
        default_factory=list,
        description="List of validation issues found"
    )
    
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested corrections or alternatives"
    )
    
    requires_human_review: bool = Field(
        default=False,
        description="Whether this product requires human review"
    )
    
    @property
    def validation_status(self) -> str:
        """Get human-readable validation status."""
        if self.is_valid:
            if self.match and self.match.is_high_confidence:
                return "validated"
            else:
                return "matched_low_confidence"
        else:
            return "failed"