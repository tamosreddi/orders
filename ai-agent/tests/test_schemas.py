"""
Tests for Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from schemas.message import MessageIntent, ExtractedProduct, MessageAnalysis
from schemas.order import OrderProduct, OrderCreation
from schemas.product import ProductMatch, ProductMatchingRequest


class TestMessageSchemas:
    """Test message-related schemas."""
    
    def test_message_intent_valid(self):
        """Test MessageIntent with valid data."""
        intent = MessageIntent(
            intent="BUY",
            confidence=0.8,
            reasoning="Clear order request"
        )
        assert intent.intent == "BUY"
        assert intent.confidence == 0.8
        assert intent.reasoning == "Clear order request"
    
    def test_message_intent_invalid_confidence(self):
        """Test MessageIntent with invalid confidence score."""
        with pytest.raises(ValidationError):
            MessageIntent(
                intent="BUY", 
                confidence=1.5,  # Invalid: > 1.0
                reasoning="Test"
            )
    
    def test_extracted_product_valid(self):
        """Test ExtractedProduct with valid data."""
        product = ExtractedProduct(
            product_name="milk",
            quantity=5,
            unit="bottles",
            original_text="5 bottles of milk",
            confidence=0.9
        )
        assert product.product_name == "milk"
        assert product.quantity == 5
        assert product.unit == "bottles"
    
    def test_extracted_product_invalid_quantity(self):
        """Test ExtractedProduct with invalid quantity."""
        with pytest.raises(ValidationError):
            ExtractedProduct(
                product_name="milk",
                quantity=0,  # Invalid: must be >= 1
                unit=None,
                original_text="milk",
                confidence=0.8
            )
    
    def test_message_analysis_complete(self):
        """Test complete MessageAnalysis."""
        intent = MessageIntent(intent="BUY", confidence=0.8, reasoning="Clear buy intent detected")
        product = ExtractedProduct(
            product_name="milk",
            quantity=2,
            unit=None,
            original_text="2 milk",
            confidence=0.7
        )
        
        analysis = MessageAnalysis(
            message_id="test-123",
            intent=intent,
            extracted_products=[product],
            customer_notes=None,
            delivery_date=None,
            processing_time_ms=150
        )
        
        assert analysis.message_id == "test-123"
        assert len(analysis.extracted_products) == 1
        assert analysis.processing_time_ms == 150


class TestOrderSchemas:
    """Test order-related schemas."""
    
    def test_order_product_minimal(self):
        """Test OrderProduct with minimal required fields."""
        product = OrderProduct(
            product_name="beer",
            quantity=2,
            unit=None,
            unit_price=None,
            line_price=None,
            ai_confidence=0.8,
            original_text="2 beer cases",
            matched_product_id=None,
            matching_confidence=None
        )
        assert product.product_name == "beer"
        assert product.quantity == 2
    
    def test_order_creation_complete(self):
        """Test complete OrderCreation."""
        product = OrderProduct(
            product_name="beer",
            quantity=2,
            unit=None,
            unit_price=None,
            line_price=None,
            ai_confidence=0.8,
            original_text="2 beer",
            matched_product_id=None,
            matching_confidence=None
        )
        
        order = OrderCreation(
            customer_id="customer-123",
            distributor_id="distributor-456",
            conversation_id=None,
            channel="WHATSAPP",
            products=[product],
            delivery_date=None,
            additional_comment=None,
            ai_confidence=0.85,
            source_message_ids=["message-789"]
        )
        
        assert order.customer_id == "customer-123"
        assert len(order.products) == 1
        assert order.channel == "WHATSAPP"


class TestProductSchemas:
    """Test product-related schemas."""
    
    def test_product_match_valid(self):
        """Test ProductMatch with valid data."""
        match = ProductMatch(
            product_id="prod-123",
            product_name="Coca Cola",
            confidence=0.95,
            match_type="EXACT",
            match_score=0.95,
            sku=None,
            unit=None,
            unit_price=None,
            category=None,
            brand=None
        )
        assert match.product_id == "prod-123"
        assert match.is_high_confidence
        assert match.is_exact_match
    
    def test_product_matching_request(self):
        """Test ProductMatchingRequest."""
        request = ProductMatchingRequest(
            customer_text="I need 5 coke bottles",
            extracted_product_name="coke",
            quantity=5,
            unit="bottles",
            customer_id=None,
            distributor_id="dist-123"
        )
        assert request.extracted_product_name == "coke"
        assert request.quantity == 5