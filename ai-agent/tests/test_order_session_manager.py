"""
Tests for Order Session Manager

Tests the core functionality of managing multi-message order sessions.

Run with: python -m pytest tests/test_order_session_manager.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.order_session_manager import (
    OrderSessionManager, 
    SessionStatus, 
    EventType,
    OrderSession,
    OrderSessionItem
)
from services.database import DatabaseService


class TestOrderSessionManager:
    """Test suite for OrderSessionManager."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database service."""
        db = Mock(spec=DatabaseService)
        return db
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        supabase = Mock()
        
        # Mock table methods
        table_mock = Mock()
        table_mock.select.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.update.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.in_.return_value = table_mock
        table_mock.gt.return_value = table_mock
        table_mock.order.return_value = table_mock
        table_mock.limit.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.execute.return_value = Mock(data=[])
        
        supabase.table.return_value = table_mock
        supabase.rpc.return_value = Mock(execute=Mock(return_value=Mock(data=0)))
        
        return supabase
    
    @pytest.fixture
    def session_manager(self, mock_supabase):
        """Create OrderSessionManager with mocked dependencies."""
        with patch('services.order_session_manager.get_supabase_client', return_value=mock_supabase):
            manager = OrderSessionManager()
            return manager
    
    def test_session_manager_initialization(self, session_manager):
        """Test that session manager initializes correctly."""
        assert session_manager.default_session_timeout == timedelta(minutes=30)
        assert session_manager.extension_timeout == timedelta(minutes=5)
        assert session_manager.supabase is not None
    
    def test_get_active_session_no_session(self, session_manager, mock_supabase):
        """Test getting active session when none exists."""
        # Setup mock to return no data
        mock_supabase.table().select().eq().in_().gt().order().limit().execute.return_value = Mock(data=[])
        
        result = session_manager.get_active_session("conversation-123")
        assert result is None
    
    def test_get_active_session_with_session(self, session_manager, mock_supabase):
        """Test getting active session when one exists."""
        # Setup mock to return session data
        session_data = {
            "id": "session-123",
            "conversation_id": "conversation-123", 
            "distributor_id": "distributor-123",
            "status": "ACTIVE",
            "started_at": "2025-08-04T10:00:00Z",
            "last_activity_at": "2025-08-04T10:05:00Z",
            "expires_at": "2025-08-04T10:30:00Z",
            "closed_at": None,
            "collected_message_ids": ["msg-1", "msg-2"],
            "total_messages_count": 2,
            "consolidated_order_data": None,
            "confidence_score": 0.8,
            "ai_processing_attempts": 1,
            "requires_review": False,
            "session_metadata": {}
        }
        
        mock_supabase.table().select().eq().in_().gt().order().limit().execute.return_value = Mock(data=[session_data])
        
        result = session_manager.get_active_session("conversation-123")
        
        assert result is not None
        assert result.id == "session-123"
        assert result.status == SessionStatus.ACTIVE
        assert result.conversation_id == "conversation-123"
        assert len(result.collected_message_ids) == 2
    
    def test_create_session_success(self, session_manager, mock_supabase):
        """Test successful session creation."""
        # Setup mock to return created session
        session_data = {
            "id": "session-123",
            "conversation_id": "conversation-123",
            "distributor_id": "distributor-123", 
            "status": "ACTIVE",
            "started_at": "2025-08-04T10:00:00Z",
            "last_activity_at": "2025-08-04T10:00:00Z",
            "expires_at": "2025-08-04T10:30:00Z",
            "closed_at": None,
            "collected_message_ids": ["msg-1"],
            "total_messages_count": 1,
            "consolidated_order_data": None,
            "confidence_score": 0.0,
            "ai_processing_attempts": 0,
            "requires_review": False,
            "session_metadata": {}
        }
        
        mock_supabase.table().insert().execute.return_value = Mock(data=[session_data])
        
        result = session_manager.create_session(
            conversation_id="conversation-123",
            distributor_id="distributor-123", 
            initial_message_id="msg-1"
        )
        
        assert result is not None
        assert result.id == "session-123"
        assert result.status == SessionStatus.ACTIVE
        assert "msg-1" in result.collected_message_ids
    
    def test_add_message_to_session_success(self, session_manager, mock_supabase):
        """Test successfully adding message to session."""
        # Setup mock session
        session_data = {
            "id": "session-123",
            "conversation_id": "conversation-123",
            "distributor_id": "distributor-123",
            "status": "ACTIVE", 
            "started_at": "2025-08-04T10:00:00Z",
            "last_activity_at": "2025-08-04T10:00:00Z",
            "expires_at": "2025-08-04T10:30:00Z",
            "closed_at": None,
            "collected_message_ids": ["msg-1"],
            "total_messages_count": 1,
            "consolidated_order_data": None,
            "confidence_score": 0.0,
            "ai_processing_attempts": 0,
            "requires_review": False,
            "session_metadata": {}
        }
        
        # Mock get_session_by_id to return the session
        with patch.object(session_manager, 'get_session_by_id') as mock_get_session:
            mock_get_session.return_value = session_manager._dict_to_session(session_data)
            
            # Mock successful update
            mock_supabase.table().update().eq().execute.return_value = Mock(data=[{}])
            
            result = session_manager.add_message_to_session("session-123", "msg-2")
            
            assert result is True
            mock_supabase.table().update.assert_called()
    
    def test_transition_status_success(self, session_manager, mock_supabase):
        """Test successful status transition."""
        # Mock successful update
        mock_supabase.table().update().eq().execute.return_value = Mock(data=[{}])
        
        result = session_manager.transition_status(
            "session-123",
            SessionStatus.COLLECTING,
            event_data={"test": "data"}
        )
        
        assert result is True
        mock_supabase.table().update.assert_called()
    
    def test_add_session_item_success(self, session_manager, mock_supabase):
        """Test successfully adding item to session."""
        # Mock successful insert
        item_data = {
            "id": "item-123",
            "session_id": "session-123",
            "product_name": "test product",
            "quantity": 2,
            "product_unit": "units"
        }
        
        mock_supabase.table().insert().execute.return_value = Mock(data=[item_data])
        
        result = session_manager.add_session_item(
            session_id="session-123",
            product_name="test product",
            quantity=Decimal('2'),
            source_message_id="msg-1",
            original_text="I need 2 test products"
        )
        
        assert result == "item-123"
    
    def test_get_session_items_success(self, session_manager, mock_supabase):
        """Test getting session items."""
        # Mock items data
        items_data = [
            {
                "id": "item-1",
                "product_name": "product 1",
                "quantity": 2,
                "product_unit": "units",
                "unit_price": None,
                "line_total": None,
                "ai_confidence": 0.8,
                "source_message_id": "msg-1",
                "original_text": "2 product 1",
                "suggested_product_id": None,
                "matching_confidence": 0.0,
                "item_status": "ACTIVE",
                "notes": None
            }
        ]
        
        mock_supabase.table().select().eq().order().execute.return_value = Mock(data=items_data)
        
        result = session_manager.get_session_items("session-123")
        
        assert len(result) == 1
        assert isinstance(result[0], OrderSessionItem)
        assert result[0].product_name == "product 1"
        assert result[0].quantity == Decimal('2')
    
    def test_close_expired_sessions(self, session_manager, mock_supabase):
        """Test closing expired sessions."""
        # Mock RPC call
        mock_supabase.rpc().execute.return_value = Mock(data=3)
        
        result = session_manager.close_expired_sessions()
        
        assert result == 3
        mock_supabase.rpc.assert_called_with("close_timed_out_sessions")
    
    def test_dict_to_session_conversion(self, session_manager):
        """Test converting database dict to OrderSession object."""
        session_data = {
            "id": "session-123",
            "conversation_id": "conversation-123",
            "distributor_id": "distributor-123",
            "status": "COLLECTING",
            "started_at": "2025-08-04T10:00:00Z",
            "last_activity_at": "2025-08-04T10:05:00Z", 
            "expires_at": "2025-08-04T10:30:00Z",
            "closed_at": None,
            "collected_message_ids": ["msg-1", "msg-2"],
            "total_messages_count": 2,
            "consolidated_order_data": {"test": "data"},
            "confidence_score": 0.85,
            "ai_processing_attempts": 1,
            "requires_review": True,
            "session_metadata": {"key": "value"}
        }
        
        result = session_manager._dict_to_session(session_data)
        
        assert isinstance(result, OrderSession)
        assert result.id == "session-123"
        assert result.status == SessionStatus.COLLECTING
        assert len(result.collected_message_ids) == 2
        assert result.confidence_score == 0.85
        assert isinstance(result.started_at, datetime)


class TestOrderSessionIntegration:
    """Integration tests for order session workflow."""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager for integration tests."""
        # Note: These tests would require actual database connection
        # For now, we'll skip them in CI/CD but they can be run locally
        pytest.skip("Integration tests require database connection")
    
    def test_full_session_lifecycle(self, session_manager):
        """Test complete session lifecycle from creation to order."""
        # This would test:
        # 1. Create session
        # 2. Add messages and items
        # 3. Transition through states
        # 4. Consolidate and create order
        # 5. Close session
        pass
    
    def test_session_timeout_handling(self, session_manager):
        """Test session timeout and cleanup."""
        # This would test:
        # 1. Create session with short timeout
        # 2. Wait for expiry
        # 3. Verify cleanup works correctly
        pass


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])