"""
Integration tests for Order Agent system.

Tests the end-to-end workflow from message processing to order creation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from schemas.message import MessageAnalysis, MessageIntent, ExtractedProduct
from schemas.order import OrderCreation, OrderProduct  
from schemas.product import CatalogProduct, ProductMatchingResponse, ProductMatch
from agents.order_agent import StreamlinedOrderProcessor
# from tools.product_matcher import initialize_product_matcher  # Not used in streamlined version
from services.database import DatabaseService


class TestOrderAgentIntegration:
    """Test the complete Order Agent workflow."""
    
    def setup_method(self):
        """Set up test fixtures for integration tests."""
        # Mock database service
        self.mock_database = Mock(spec=DatabaseService)
        
        # Create sample catalog products
        self.catalog_products = [
            CatalogProduct(
                id="1",
                name="Coca Cola",
                sku="COKE-500",
                description=None,
                unit="bottles",
                unit_price=Decimal("2.50"),
                category="beverages",
                brand="Coca Cola",
                aliases=["coke", "coca", "cola"]
            ),
            CatalogProduct(
                id="2",
                name="Milk",
                sku="MILK-1L",
                description=None,
                unit="bottles",
                unit_price=Decimal("3.00"),
                category="dairy",
                brand="Generic",
                aliases=["leche"]
            )
        ]
        
        # Create streamlined Order Agent processor (no product matcher needed)
        self.processor = StreamlinedOrderProcessor(
            database=self.mock_database,
            distributor_id="test-distributor"
        )
    
    @pytest.mark.asyncio
    async def test_buy_intent_order_creation_workflow(self):
        """Test complete workflow from BUY message to order creation."""
        # Mock message representing customer order
        test_message = {
            'id': 'msg-123',
            'content': 'I need 5 bottles of coca cola and 2 bottles of milk',
            'customer_id': 'customer-456',
            'conversation_id': 'conv-789',
            'channel': 'WHATSAPP'
        }
        
        # Mock external dependencies
        with patch('tools.supabase_tools.update_message_ai_data') as mock_update, \
             patch('tools.supabase_tools.create_order') as mock_create_order, \
             patch.object(self.processor, '_analyze_message_intent') as mock_analyze:
            
            # Mock intent analysis result
            mock_analyze.return_value = MessageAnalysis(
                message_id="msg-123",
                intent=MessageIntent(
                    intent="BUY",
                    confidence=0.9,
                    reasoning="Clear order request with products and quantities"
                ),
                extracted_products=[
                    ExtractedProduct(
                        product_name="coca cola",
                        quantity=5,
                        unit="bottles",
                        original_text="5 bottles of coca cola",
                        confidence=0.85
                    ),
                    ExtractedProduct(
                        product_name="milk", 
                        quantity=2,
                        unit="bottles",
                        original_text="2 bottles of milk",
                        confidence=0.90
                    )
                ],
                customer_notes=None,
                delivery_date=None,
                processing_time_ms=0
            )
            
            # Mock successful order creation
            mock_create_order.return_value = "order-123"
            mock_update.return_value = None
            
            # Process the message
            result = await self.processor.process_message(test_message)
            
            # Verify the workflow completed successfully
            assert result is not None
            assert result.intent.intent == "BUY"
            assert result.intent.confidence == 0.9
            assert len(result.extracted_products) == 2
            
            # Verify external calls were made
            mock_analyze.assert_called_once()
            mock_update.assert_called_once()
            mock_create_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_question_intent_no_order_creation(self):
        """Test that QUESTION intents don't create orders."""
        test_message = {
            'id': 'msg-456',
            'content': 'What is the price of milk?',
            'customer_id': 'customer-789',
            'conversation_id': 'conv-123',
            'channel': 'WHATSAPP'
        }
        
        with patch('tools.supabase_tools.update_message_ai_data') as mock_update, \
             patch('tools.supabase_tools.create_order') as mock_create_order, \
             patch.object(self.processor, '_analyze_message_intent') as mock_analyze:
            
            # Mock question intent analysis
            mock_analyze.return_value = MessageAnalysis(
                message_id="msg-456",
                intent=MessageIntent(
                    intent="QUESTION",
                    confidence=0.85,
                    reasoning="Customer asking about pricing information"
                ),
                extracted_products=[],
                customer_notes=None,
                delivery_date=None,
                processing_time_ms=0
            )
            
            mock_update.return_value = None
            
            # Process the message
            result = await self.processor.process_message(test_message)
            
            # Verify no order was created
            assert result is not None
            assert result.intent.intent == "QUESTION"
            assert len(result.extracted_products) == 0
            
            # Verify order creation was NOT called
            mock_create_order.assert_not_called()
            mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_low_confidence_no_order_creation(self):
        """Test that low confidence extractions don't create orders."""
        test_message = {
            'id': 'msg-789',
            'content': 'maybe some stuff',  # Ambiguous message
            'customer_id': 'customer-123',
            'conversation_id': 'conv-456',
            'channel': 'WHATSAPP'
        }
        
        with patch('tools.supabase_tools.update_message_ai_data') as mock_update, \
             patch('tools.supabase_tools.create_order') as mock_create_order, \
             patch.object(self.processor, '_analyze_message_intent') as mock_analyze:
            
            # Mock low confidence analysis
            mock_analyze.return_value = MessageAnalysis(
                message_id="msg-789",
                intent=MessageIntent(
                    intent="BUY",
                    confidence=0.4,  # Low confidence
                    reasoning="Ambiguous message, unclear intent"
                ),
                extracted_products=[
                    ExtractedProduct(
                        product_name="stuff",
                        quantity=1,
                        unit=None,
                        original_text="some stuff",
                        confidence=0.3  # Very low confidence
                    )
                ],
                customer_notes=None,
                delivery_date=None,
                processing_time_ms=0
            )
            
            mock_update.return_value = None
            
            # Process the message
            result = await self.processor.process_message(test_message)
            
            # Verify no order was created due to low confidence
            assert result is not None
            assert result.intent.intent == "BUY"
            assert not result.is_high_confidence  # Should be low confidence
            
            # Verify order creation was NOT called
            mock_create_order.assert_not_called()
            mock_update.assert_called_once()
    
    def test_system_components_integration(self):
        """Test that all system components integrate properly."""
        # Verify all components are properly initialized
        assert self.processor.database is not None
        assert self.processor.product_matcher is not None
        assert self.processor.distributor_id == "test-distributor"
        
        # Verify product matcher has catalog
        assert len(self.product_matcher.catalog_products) == 2
        
        # Verify dependencies are properly injected
        assert self.processor.deps.database == self.mock_database
        assert self.processor.deps.product_matcher == self.product_matcher
        assert self.processor.deps.distributor_id == "test-distributor"