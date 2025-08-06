"""
Autonomous agent schemas for goal-oriented order processing.

Defines context management, action representation, and result structures
for the autonomous order agent that makes intelligent decisions.
"""

from __future__ import annotations as _annotations

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum

from schemas.message import MessageIntent, ExtractedProduct
from schemas.order import OrderProduct
from schemas.goals import BusinessGoal, ActionEvaluation


class AutonomousActionType(str, Enum):
    """Types of actions the autonomous agent can take."""
    DO_NOTHING = "do_nothing"  # No action needed - let conversation flow naturally
    CREATE_ORDER = "create_order"
    ASK_CLARIFICATION = "ask_clarification" 
    SUGGEST_PRODUCTS = "suggest_products"
    PROVIDE_PRICING = "provide_pricing"  # Provide product pricing information
    CHECK_AVAILABILITY = "check_availability"  # Check product availability/stock
    REQUEST_PRICING = "request_pricing"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    PROVIDE_INFORMATION = "provide_information"
    UPDATE_CUSTOMER_PREFERENCES = "update_customer_preferences"


class CustomerPreference(BaseModel):
    """Individual customer preference learned from interactions."""
    
    preference_type: str = Field(
        ...,
        description="Type of preference (product, timing, communication, etc.)"
    )
    
    value: str = Field(
        ...,
        description="Preference value or description"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in this preference"
    )
    
    learned_from: str = Field(
        ...,
        description="Source of this preference (conversation_id, order_id, etc.)"
    )
    
    created_at: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this preference was learned"
    )


class InventoryStatus(BaseModel):
    """Current inventory status for decision making."""
    
    product_id: str = Field(
        ...,
        description="Product ID"
    )
    
    product_name: str = Field(
        ...,
        description="Product name"
    )
    
    in_stock: bool = Field(
        ...,
        description="Whether product is currently in stock"
    )
    
    stock_quantity: Optional[int] = Field(
        None,
        description="Current stock quantity if available"
    )
    
    estimated_restock_date: Optional[str] = Field(
        None,
        description="When product will be back in stock"
    )
    
    substitute_products: List[str] = Field(
        default_factory=list,
        description="List of substitute product IDs"
    )


class TimeContext(BaseModel):
    """Temporal context for decision making."""
    
    current_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Current timestamp"
    )
    
    business_hours: bool = Field(
        ...,
        description="Whether it's currently business hours"
    )
    
    day_of_week: str = Field(
        ...,
        description="Current day of the week"
    )
    
    is_holiday: bool = Field(
        default=False,
        description="Whether today is a holiday"
    )
    
    peak_hours: bool = Field(
        default=False,
        description="Whether it's currently peak business hours"
    )


class AutonomousAgentContext(BaseModel):
    """
    Rich context for autonomous agent decision making.
    
    Contains all information needed for the agent to make intelligent
    decisions about order processing and customer interactions.
    """
    
    # Customer Information
    customer_id: str = Field(
        ...,
        description="ID of the customer"
    )
    
    customer_name: Optional[str] = Field(
        None,
        description="Customer name if available"
    )
    
    customer_preferences: List[CustomerPreference] = Field(
        default_factory=list,
        description="Learned customer preferences"
    )
    
    # Conversation Context
    conversation_id: str = Field(
        ...,
        description="ID of the current conversation"
    )
    
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent messages in this conversation"
    )
    
    current_message: Dict[str, Any] = Field(
        ...,
        description="The current message being processed"
    )
    
    # Business Context
    distributor_id: str = Field(
        ...,
        description="ID of the distributor"
    )
    
    business_goals: List[BusinessGoal] = Field(
        ...,
        description="Current business goals with weights"
    )
    
    inventory_status: List[InventoryStatus] = Field(
        default_factory=list,
        description="Current inventory status for relevant products"
    )
    
    time_context: TimeContext = Field(
        ...,
        description="Temporal context for decision making"
    )
    
    # Previous AI Analysis
    extracted_intent: Optional[MessageIntent] = Field(
        None,
        description="AI-extracted intent from current message"
    )
    
    extracted_products: List[ExtractedProduct] = Field(
        default_factory=list,
        description="AI-extracted products from current message"
    )
    
    # Order History
    recent_orders: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Customer's recent orders for context"
    )
    
    order_session_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Current order session context if available"
    )
    
    @property
    def has_buy_intent(self) -> bool:
        """Check if current message has buy intent."""
        return self.extracted_intent and self.extracted_intent.intent == "BUY"
    
    @property
    def has_extracted_products(self) -> bool:
        """Check if any products were extracted."""
        return len(self.extracted_products) > 0
    
    @property
    def customer_order_history_length(self) -> int:
        """Get number of recent orders."""
        return len(self.recent_orders)


class AutonomousAction(BaseModel):
    """
    Specific action the autonomous agent can take.
    
    Represents a potential action with parameters and expected outcomes
    that can be evaluated against business goals.
    """
    
    action_type: AutonomousActionType = Field(
        ...,
        description="Type of action to take"
    )
    
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters needed to execute this action"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in this action choice"
    )
    
    reasoning: str = Field(
        ...,
        min_length=1,
        description="Why the agent chose this action"
    )
    
    expected_outcomes: List[str] = Field(
        default_factory=list,
        description="Expected results of taking this action"
    )
    
    estimated_impact: Dict[str, float] = Field(
        default_factory=dict,
        description="Estimated impact on different metrics"
    )
    
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Prerequisites that must be met before taking this action"
    )
    
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Potential risks or downsides of this action"
    )
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this action has high confidence."""
        return self.confidence >= 0.8
    
    @property
    def is_order_creating_action(self) -> bool:
        """Check if this action creates an order."""
        return self.action_type == AutonomousActionType.CREATE_ORDER
    
    @property
    def requires_customer_response(self) -> bool:
        """Check if this action requires customer response."""
        return self.action_type in [
            AutonomousActionType.ASK_CLARIFICATION,
            AutonomousActionType.SUGGEST_PRODUCTS,
            AutonomousActionType.REQUEST_PRICING
        ]


class AutonomousDecision(BaseModel):
    """
    Decision made by the autonomous agent.
    
    Contains the chosen action, evaluation details, and execution plan.
    """
    
    chosen_action: AutonomousAction = Field(
        ...,
        description="The action chosen by the agent"
    )
    
    action_evaluation: ActionEvaluation = Field(
        ...,
        description="Evaluation of the chosen action against business goals"
    )
    
    alternative_actions: List[AutonomousAction] = Field(
        default_factory=list,
        description="Other actions that were considered"
    )
    
    alternative_evaluations: List[ActionEvaluation] = Field(
        default_factory=list,
        description="Evaluations of alternative actions"
    )
    
    decision_reasoning: str = Field(
        ...,
        min_length=1,
        description="High-level reasoning for this decision"
    )
    
    decision_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this decision was made"
    )
    
    confidence_factors: List[str] = Field(
        default_factory=list,
        description="Factors that contributed to confidence level"
    )
    
    uncertainty_factors: List[str] = Field(
        default_factory=list,
        description="Factors that created uncertainty"
    )
    
    @property
    def is_autonomous_decision(self) -> bool:
        """Check if this decision can be executed autonomously."""
        return (self.action_evaluation.confidence >= 0.8 and 
                self.action_evaluation.overall_score >= 0.7)
    
    @property
    def should_escalate(self) -> bool:
        """Check if this decision should be escalated to human."""
        return (self.action_evaluation.confidence < 0.6 or
                self.chosen_action.action_type == AutonomousActionType.ESCALATE_TO_HUMAN)


class AutonomousResult(BaseModel):
    """
    Result of autonomous agent processing.
    
    Contains the decision made, execution status, and learning insights.
    """
    
    message_id: str = Field(
        ...,
        description="ID of the message that was processed"
    )
    
    decision: Optional[AutonomousDecision] = Field(
        None,
        description="Decision made by the autonomous agent"
    )
    
    execution_status: str = Field(
        ...,
        description="Status of decision execution (planned, executing, completed, failed)"
    )
    
    execution_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Result of executing the decision"
    )
    
    learning_insights: List[str] = Field(
        default_factory=list,
        description="Insights learned from this interaction"
    )
    
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Time taken to process and decide"
    )
    
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback to existing system was used"
    )
    
    fallback_reason: Optional[str] = Field(
        None,
        description="Reason for fallback if used"
    )
    
    created_order_id: Optional[str] = Field(
        None,
        description="ID of order created if applicable"
    )
    
    customer_response_sent: Optional[str] = Field(
        None,
        description="Response sent to customer if applicable"
    )
    
    @property
    def was_successful(self) -> bool:
        """Check if processing was successful."""
        return self.execution_status in ["completed", "planned"]
    
    @property
    def created_order(self) -> bool:
        """Check if an order was created."""
        return self.created_order_id is not None


class AutonomousAgentDeps(BaseModel):
    """
    Dependencies for the autonomous agent.
    
    Following the pattern from examples/example_pydantic_ai.py for dependency injection.
    """
    
    database: Any = Field(
        ...,
        description="Database service instance"
    )
    
    distributor_id: str = Field(
        ...,
        description="Current distributor ID"
    )
    
    goal_evaluator: Any = Field(
        ...,
        description="Goal evaluator service instance"
    )
    
    memory_service: Any = Field(
        ...,
        description="Conversation memory service instance"
    )
    
    business_goals: List[BusinessGoal] = Field(
        ...,
        description="Current business goals configuration"
    )
    
    feature_flags: Dict[str, Any] = Field(
        default_factory=dict,
        description="Feature flags for the agent"
    )
    
    class Config:
        """Allow arbitrary types for service instances."""
        arbitrary_types_allowed = True


class LearningEvent(BaseModel):
    """
    Event for learning and improving autonomous decisions.
    
    Tracks outcomes to improve future decision making.
    """
    
    event_type: str = Field(
        ...,
        description="Type of learning event (order_success, customer_complaint, etc.)"
    )
    
    context_summary: str = Field(
        ...,
        description="Summary of the context when event occurred"
    )
    
    action_taken: str = Field(
        ...,
        description="Action that was taken"
    )
    
    outcome: str = Field(
        ...,
        description="Actual outcome of the action"
    )
    
    expected_outcome: str = Field(
        ...,
        description="What was expected to happen"
    )
    
    success_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Measured success metrics"
    )
    
    lesson_learned: str = Field(
        ...,
        description="What was learned from this event"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this event occurred"
    )
    
    customer_id: str = Field(
        ...,
        description="Customer involved in this event"
    )
    
    distributor_id: str = Field(
        ...,
        description="Distributor involved in this event"
    )


def create_simple_action(
    action_type: AutonomousActionType,
    parameters: Dict[str, Any],
    reasoning: str,
    confidence: float = 0.8
) -> AutonomousAction:
    """
    Helper function to create simple autonomous actions.
    
    Args:
        action_type: Type of action to create
        parameters: Action parameters
        reasoning: Reason for this action
        confidence: Confidence level (default 0.8)
        
    Returns:
        AutonomousAction: Configured action
    """
    return AutonomousAction(
        action_type=action_type,
        parameters=parameters,
        confidence=confidence,
        reasoning=reasoning,
        expected_outcomes=[f"Execute {action_type} successfully"],
    )