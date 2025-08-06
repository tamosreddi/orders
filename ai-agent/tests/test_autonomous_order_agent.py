"""
Comprehensive tests for the autonomous order agent system.

Tests all components including goal evaluation, memory learning, action execution,
feature flags, and end-to-end autonomous decision making.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, List, Any

# Import the components we're testing
from schemas.goals import (
    BusinessGoal, BusinessGoalType, ActionEvaluation, GoalConfiguration,
    create_default_goal_configuration
)
from schemas.autonomous_agent import (
    AutonomousAction, AutonomousActionType, AutonomousAgentContext,
    AutonomousDecision, AutonomousResult, CustomerPreference, create_simple_action
)
from services.goal_evaluator import GoalEvaluator
from services.conversation_memory import ConversationMemory
from agents.autonomous_order_agent import AutonomousOrderAgent
from agents.agent_factory import AgentFactory, AgentType
from config.feature_flags import (
    FeatureFlagConfiguration, FeatureFlag, FeatureFlagStatus,
    AutonomousAgentFeature, create_default_feature_flags
)
from tools.autonomous_actions import execute_autonomous_action


class TestBusinessGoalsSchema:
    """Test business goals and evaluation schemas."""
    
    def test_business_goal_creation(self):
        """Test creating a business goal with validation."""
        goal = BusinessGoal(
            name=BusinessGoalType.CUSTOMER_SATISFACTION,
            weight=0.4,
            description="Ensure customers are satisfied",
            metrics=["response_time", "accuracy"]
        )
        
        assert goal.name == BusinessGoalType.CUSTOMER_SATISFACTION
        assert goal.weight == 0.4
        assert goal.is_primary_goal  # weight > 0.3
        assert len(goal.metrics) == 2
    
    def test_goal_configuration_validation(self):
        """Test goal configuration weight validation."""
        goals = [
            BusinessGoal(
                name=BusinessGoalType.CUSTOMER_SATISFACTION,
                weight=0.5,
                description="Customer satisfaction"
            ),
            BusinessGoal(
                name=BusinessGoalType.ORDER_VALUE,
                weight=0.5,
                description="Order value"
            )
        ]
        
        config = GoalConfiguration(
            distributor_id="test_distributor",
            goals=goals
        )
        
        assert len(config.goals) == 2
        assert len(config.primary_goals) == 2  # Both have weight > 0.3
    
    def test_action_evaluation_creation(self):
        """Test action evaluation with goal scores."""
        evaluation = ActionEvaluation(
            action_name=AutonomousActionType.CREATE_ORDER,
            goal_scores={
                "customer_satisfaction": 0.9,
                "order_value": 0.8
            },
            overall_score=0.85,
            reasoning="High confidence order creation",
            confidence=0.9
        )
        
        assert evaluation.is_high_confidence
        assert evaluation.is_recommended_action
    
    def test_default_goal_configurations(self):
        """Test default goal configuration creation."""
        balanced_config = create_default_goal_configuration("test_dist", "balanced")
        revenue_config = create_default_goal_configuration("test_dist", "revenue")
        service_config = create_default_goal_configuration("test_dist", "service")
        
        # Check that weights sum to ~1.0
        for config in [balanced_config, revenue_config, service_config]:
            total_weight = sum(goal.weight for goal in config.goals)
            assert 0.99 <= total_weight <= 1.01


class TestGoalEvaluator:
    """Test goal evaluation service."""
    
    @pytest.fixture
    def goal_evaluator(self):
        """Create goal evaluator instance."""
        return GoalEvaluator()
    
    @pytest.fixture
    def business_goals(self):
        """Create test business goals."""
        return create_default_goal_configuration("test_dist", "balanced").goals
    
    @pytest.fixture
    def test_context(self):
        """Create test agent context."""
        return AutonomousAgentContext(
            customer_id="test_customer",
            conversation_id="test_conv",
            current_message={"content": "quiero dos botellas de leche", "id": "msg1"},
            distributor_id="test_dist",
            business_goals=[],
            time_context={
                "business_hours": True,
                "peak_hours": False,
                "day_of_week": "Monday"
            }
        )
    
    @pytest.mark.asyncio
    async def test_goal_evaluation_scoring(self, goal_evaluator, business_goals, test_context):
        """Test goal evaluator produces consistent scores."""
        action = create_simple_action(
            AutonomousActionType.CREATE_ORDER,
            {"products": [{"product_name": "leche", "quantity": 2}]},
            "Customer wants to buy milk",
            confidence=0.9
        )
        
        evaluation = await goal_evaluator.evaluate_action(action, test_context, business_goals)
        
        assert 0.0 <= evaluation.overall_score <= 1.0
        assert 0.0 <= evaluation.confidence <= 1.0
        assert evaluation.reasoning is not None
        assert len(evaluation.goal_scores) == len(business_goals)
        
        # All goal scores should be in valid range
        for score in evaluation.goal_scores.values():
            assert 0.0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_customer_satisfaction_scoring(self, goal_evaluator, test_context):
        """Test customer satisfaction goal scoring."""
        # Test high satisfaction action (create order with buy intent)
        test_context.extracted_products = [Mock(product_name="leche", quantity=2)]
        
        high_satisfaction_action = create_simple_action(
            AutonomousActionType.CREATE_ORDER,
            {"products": [{"product_name": "leche", "quantity": 2}]},
            "Fulfilling customer order",
            confidence=0.9
        )
        
        score = await goal_evaluator._score_customer_satisfaction(
            high_satisfaction_action, test_context
        )
        
        assert score >= 0.8  # Should be high for order fulfillment
        
        # Test lower satisfaction action (escalation)
        escalation_action = create_simple_action(
            AutonomousActionType.ESCALATE_TO_HUMAN,
            {"reason": "Unable to process"},
            "Escalating to human",
            confidence=0.8
        )
        
        escalation_score = await goal_evaluator._score_customer_satisfaction(
            escalation_action, test_context
        )
        
        assert escalation_score < score  # Escalation should score lower than direct fulfillment
    
    @pytest.mark.asyncio
    async def test_order_value_scoring(self, goal_evaluator, test_context):
        """Test order value goal scoring."""
        # Single product order
        single_product_context = test_context
        single_product_context.extracted_products = [Mock(product_name="leche", quantity=1)]
        
        single_action = create_simple_action(
            AutonomousActionType.CREATE_ORDER,
            {"products": [{"product_name": "leche", "quantity": 1}]},
            "Single product order"
        )
        
        single_score = await goal_evaluator._score_order_value(single_action, single_product_context)
        
        # Multiple product order
        multi_product_context = test_context
        multi_product_context.extracted_products = [
            Mock(product_name="leche", quantity=2),
            Mock(product_name="pan", quantity=1)
        ]
        
        multi_action = create_simple_action(
            AutonomousActionType.CREATE_ORDER,
            {"products": [{"product_name": "leche", "quantity": 2}, {"product_name": "pan", "quantity": 1}]},
            "Multiple product order"
        )
        
        multi_score = await goal_evaluator._score_order_value(multi_action, multi_product_context)
        
        assert multi_score > single_score  # Multiple products should score higher


class TestFeatureFlags:
    """Test feature flag configuration and management."""
    
    def test_feature_flag_creation(self):
        """Test creating feature flags with validation."""
        flag = FeatureFlag(
            name="test_feature",
            status=FeatureFlagStatus.GRADUAL_ROLLOUT,
            rollout_percentage=25.0,
            description="Test feature for rollout"
        )
        
        assert flag.name == "test_feature"
        assert flag.status == FeatureFlagStatus.GRADUAL_ROLLOUT
        assert flag.rollout_percentage == 25.0
    
    def test_feature_flag_configuration(self):
        """Test feature flag configuration and evaluation."""
        config = create_default_feature_flags()
        
        # Test disabled feature
        assert not config.is_feature_enabled(
            AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
            "test_distributor"
        )
        
        # Enable global autonomous and test enabled feature with explicit distributor
        config.global_autonomous_enabled = True
        config.flags[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED].enabled_for_distributors = ["test_distributor"]
        
        assert config.is_feature_enabled(
            AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
            "test_distributor"
        )
    
    def test_rollout_percentage_calculation(self):
        """Test percentage-based rollout calculation."""
        config = create_default_feature_flags()
        
        # Set up gradual rollout
        config.flags[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED].status = FeatureFlagStatus.GRADUAL_ROLLOUT
        config.flags[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED].rollout_percentage = 50.0
        
        # Test deterministic rollout (should be consistent for same inputs)
        result1 = config.is_feature_enabled(
            AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
            "test_distributor",
            "test_customer"
        )
        
        result2 = config.is_feature_enabled(
            AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
            "test_distributor",
            "test_customer"
        )
        
        assert result1 == result2  # Should be deterministic


class TestConversationMemory:
    """Test conversation memory service."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database service."""
        db = AsyncMock()
        db.execute_query = AsyncMock()
        db.insert_single = AsyncMock()
        db.update_single = AsyncMock()
        return db
    
    @pytest.fixture
    def memory_service(self, mock_database):
        """Create conversation memory service."""
        return ConversationMemory(mock_database)
    
    @pytest.mark.asyncio
    async def test_customer_preference_learning(self, memory_service, mock_database):
        """Test learning customer preferences."""
        preference = CustomerPreference(
            preference_type="product_preference",
            value="organic_products",
            confidence=0.8,
            learned_from="conversation_123"
        )
        
        # Mock database responses
        mock_database.execute_query.return_value = []  # No existing preferences
        mock_database.insert_single.return_value = {"id": "pref_123"}
        
        result = await memory_service.learn_customer_preference(
            "customer_123", "distributor_123", preference
        )
        
        assert result is True
        mock_database.insert_single.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_agent_context(self, memory_service, mock_database):
        """Test building comprehensive agent context."""
        # Mock database responses
        mock_database.execute_query.return_value = []
        
        message_data = {
            "id": "msg_123",
            "content": "quiero leche",
            "customer_id": "customer_123",
            "conversation_id": "conv_123"
        }
        
        business_goals = create_default_goal_configuration("test_dist", "balanced").goals
        
        context = await memory_service.build_agent_context(
            message_data, "distributor_123", business_goals
        )
        
        assert context.customer_id == "customer_123"
        assert context.conversation_id == "conv_123"
        assert context.current_message == message_data
        assert len(context.business_goals) == len(business_goals)


class TestAutonomousOrderAgent:
    """Test autonomous order agent integration."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database service."""
        return AsyncMock()
    
    @pytest.fixture
    def autonomous_agent(self, mock_database):
        """Create autonomous order agent."""
        return AutonomousOrderAgent(mock_database, "test_distributor")
    
    @pytest.mark.asyncio
    async def test_autonomous_agent_initialization(self, autonomous_agent):
        """Test autonomous agent initialization."""
        assert autonomous_agent.distributor_id == "test_distributor"
        assert autonomous_agent.goal_evaluator is not None
        assert autonomous_agent.memory_service is not None
        assert len(autonomous_agent.business_goals) > 0
    
    @pytest.mark.asyncio
    async def test_feature_flag_integration(self, autonomous_agent):
        """Test feature flag integration in autonomous agent."""
        # Test when autonomous agent is disabled
        with patch('agents.autonomous_order_agent.feature_flags') as mock_flags:
            mock_flags.is_feature_enabled.return_value = False
            mock_flags.fallback_enabled = True
            
            message_data = {
                "id": "msg_123",
                "content": "test message",
                "customer_id": "customer_123"
            }
            
            # Mock the fallback method
            with patch.object(autonomous_agent, '_fallback_to_existing_agent') as mock_fallback:
                mock_fallback.return_value = Mock()
                
                result = await autonomous_agent.process_message(message_data)
                
                # Should use fallback when autonomous is disabled
                mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_simple_actions(self, autonomous_agent):
        """Test action generation based on message content."""
        # Create test context with buy intent
        context = AutonomousAgentContext(
            customer_id="test_customer",
            conversation_id="test_conv",
            current_message={"content": "quiero dos botellas de leche", "id": "msg1"},
            distributor_id="test_dist",
            business_goals=autonomous_agent.business_goals,
            time_context={"business_hours": True}
        )
        
        actions = await autonomous_agent._generate_simple_actions(context)
        
        assert len(actions) > 0
        
        # Should generate order creation action for buy intent
        action_types = [action.action_type for action in actions]
        assert AutonomousActionType.CREATE_ORDER in action_types


class TestAgentFactory:
    """Test agent factory for intelligent agent selection."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database service."""
        return AsyncMock()
    
    @pytest.fixture
    def agent_factory(self, mock_database):
        """Create agent factory."""
        return AgentFactory(mock_database, "test_distributor")
    
    @pytest.mark.asyncio
    async def test_agent_selection_with_feature_flags(self, agent_factory):
        """Test agent selection based on feature flags."""
        # Test autonomous agent selection when enabled
        with patch('agents.agent_factory.is_autonomous_agent_enabled') as mock_enabled:
            mock_enabled.return_value = True
            
            agent = await agent_factory.create_agent("test_customer")
            
            assert agent.__class__.__name__ == "AutonomousOrderAgent"
        
        # Test streamlined agent selection when disabled
        with patch('agents.agent_factory.is_autonomous_agent_enabled') as mock_enabled:
            mock_enabled.return_value = False
            
            agent = await agent_factory.create_agent("test_customer")
            
            assert agent.__class__.__name__ == "StreamlinedOrderProcessor"
    
    @pytest.mark.asyncio
    async def test_forced_agent_type(self, agent_factory):
        """Test forcing specific agent type."""
        # Force autonomous agent
        agent = await agent_factory.create_agent(
            "test_customer", 
            force_agent_type=AgentType.AUTONOMOUS
        )
        
        assert agent.__class__.__name__ == "AutonomousOrderAgent"
        
        # Force streamlined agent
        agent = await agent_factory.create_agent(
            "test_customer",
            force_agent_type=AgentType.STREAMLINED
        )
        
        assert agent.__class__.__name__ == "StreamlinedOrderProcessor"
    
    @pytest.mark.asyncio
    async def test_agent_health_status(self, agent_factory):
        """Test agent factory health status."""
        health_status = await agent_factory.get_agent_health_status()
        
        assert "factory_status" in health_status
        assert "distributor_id" in health_status
        assert "feature_flags" in health_status
        assert "agents" in health_status
        
        assert health_status["distributor_id"] == "test_distributor"


class TestAutonomousActions:
    """Test autonomous action execution."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database service."""
        return AsyncMock()
    
    @pytest.fixture
    def test_context(self):
        """Create test context for action execution."""
        return AutonomousAgentContext(
            customer_id="test_customer",
            conversation_id="test_conv",
            current_message={"content": "quiero leche", "id": "msg1"},
            distributor_id="test_dist",
            business_goals=[],
            time_context={"business_hours": True}
        )
    
    @pytest.mark.asyncio
    async def test_create_order_action_execution(self, mock_database, test_context):
        """Test order creation action execution."""
        action = create_simple_action(
            AutonomousActionType.CREATE_ORDER,
            {
                "products": [{"product_name": "leche", "quantity": 2}],
                "customer_notes": "Autonomous order"
            },
            "Customer wants milk"
        )
        
        # Mock successful order creation
        with patch('tools.autonomous_actions.create_order') as mock_create_order:
            mock_create_order.return_value = "order_123"
            
            with patch('tools.autonomous_actions.create_distributor_message') as mock_message:
                mock_message.return_value = "msg_123"
                
                result = await execute_autonomous_action(action, test_context, mock_database)
                
                assert result["success"] is True
                assert "order_id" in result
                mock_create_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ask_clarification_action_execution(self, mock_database, test_context):
        """Test clarification request action execution."""
        action = create_simple_action(
            AutonomousActionType.ASK_CLARIFICATION,
            {
                "question": "¿Qué productos necesitas?",
                "question_type": "product_specification"
            },
            "Need product clarification"
        )
        
        # Mock successful message sending
        with patch('tools.autonomous_actions.create_distributor_message') as mock_message:
            mock_message.return_value = "msg_123"
            
            result = await execute_autonomous_action(action, test_context, mock_database)
            
            assert result["success"] is True
            assert "message_id" in result
            mock_message.assert_called_once()


class TestEndToEndIntegration:
    """Test end-to-end autonomous agent processing."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database service."""
        db = AsyncMock()
        
        # Mock database responses for typical operations
        db.execute_query.return_value = []
        db.insert_single.return_value = {"id": "test_id"}
        db.update_single.return_value = {"id": "test_id"}
        
        return db
    
    @pytest.mark.asyncio
    async def test_full_autonomous_processing_flow(self, mock_database):
        """Test complete autonomous processing flow."""
        # Enable autonomous agent for this test
        with patch('config.feature_flags.feature_flags') as mock_flags:
            mock_flags.is_feature_enabled.return_value = True
            mock_flags.global_autonomous_enabled = True
            mock_flags.fallback_enabled = True
            
            # Create agent factory and process message
            factory = AgentFactory(mock_database, "test_distributor")
            
            message_data = {
                "id": "msg_123",
                "content": "quiero dos botellas de leche",
                "customer_id": "customer_123",
                "conversation_id": "conv_123",
                "channel": "WHATSAPP"
            }
            
            # Mock successful autonomous processing
            with patch.object(factory, '_get_autonomous_agent') as mock_get_agent:
                mock_agent = AsyncMock()
                mock_result = AutonomousResult(
                    message_id="msg_123",
                    decision=Mock(),
                    execution_status="completed",
                    processing_time_ms=500,
                    fallback_used=False
                )
                mock_agent.process_message.return_value = mock_result
                mock_get_agent.return_value = mock_agent
                
                result = await factory.process_message_with_best_agent(message_data)
                
                assert result is not None
                assert result.message_id == "msg_123"
                assert result.execution_status == "completed"
                assert not result.fallback_used


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])