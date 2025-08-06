"""
Business goals and action evaluation schemas for autonomous decision making.

Defines the goal-oriented decision making framework where actions are evaluated
against multiple business objectives with weighted scoring.
"""

from __future__ import annotations as _annotations

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any
from enum import Enum
import os


class BusinessGoalType(str, Enum):
    """Core business goal types for autonomous decision making."""
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    ORDER_VALUE = "order_value" 
    EFFICIENCY = "efficiency"
    RELATIONSHIP_BUILDING = "relationship_building"


class BusinessGoal(BaseModel):
    """
    Individual business goal with weight and metrics.
    
    Used to evaluate actions against specific business objectives
    with configurable importance weights.
    """
    
    name: BusinessGoalType = Field(
        ...,
        description="Type of business goal"
    )
    
    weight: float = Field(
        ...,
        ge=0.0, 
        le=1.0,
        description="Importance weight for this goal (0.0-1.0)"
    )
    
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable description of this goal"
    )
    
    metrics: List[str] = Field(
        default_factory=list,
        description="List of metrics used to measure this goal"
    )
    
    @field_validator('weight')
    @classmethod
    def validate_weight_precision(cls, v):
        """Ensure weight has reasonable precision."""
        return round(v, 3)  # Round to 3 decimal places
    
    @property
    def is_primary_goal(self) -> bool:
        """Check if this is a primary goal (weight > 0.3)."""
        return self.weight > 0.3


class ActionEvaluation(BaseModel):
    """
    Evaluation of a specific action against all business goals.
    
    Contains goal-specific scores, overall weighted score, and reasoning
    for transparent decision making.
    """
    
    action_name: str = Field(
        ...,
        min_length=1,
        description="Name of the action being evaluated"
    )
    
    goal_scores: Dict[str, float] = Field(
        ...,
        description="Goal name -> score (0.0-1.0) mapping"
    )
    
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted overall score for this action"
    )
    
    reasoning: str = Field(
        ...,
        min_length=1,
        description="Explanation of why this action scored this way"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in this evaluation"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for evaluation context"
    )
    
    @field_validator('goal_scores')
    @classmethod
    def validate_goal_scores(cls, v):
        """Ensure all goal scores are in valid range."""
        for goal_name, score in v.items():
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Goal score for {goal_name} must be between 0.0 and 1.0, got {score}")
        return v
    
    @field_validator('overall_score')
    @classmethod
    def validate_overall_score_range(cls, v):
        """Ensure overall score is in valid range."""
        return max(0.0, min(1.0, round(v, 3)))
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence_range(cls, v):
        """Ensure confidence is in valid range."""
        return max(0.0, min(1.0, round(v, 3)))
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this evaluation is high confidence."""
        return self.confidence >= 0.8
    
    @property
    def is_recommended_action(self) -> bool:
        """Check if this action is recommended based on score and confidence."""
        return self.overall_score >= 0.7 and self.confidence >= 0.7


class GoalConfiguration(BaseModel):
    """
    Configuration for business goals per distributor.
    
    Allows customizing goal weights and priorities for different
    business contexts and distributor preferences.
    """
    
    distributor_id: str = Field(
        ...,
        min_length=1,
        description="Distributor ID this configuration applies to"
    )
    
    goals: List[BusinessGoal] = Field(
        ...,
        min_length=1,
        description="List of business goals with weights"
    )
    
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for autonomous actions"
    )
    
    score_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum overall score threshold for recommended actions"
    )
    
    created_at: Optional[str] = Field(
        None,
        description="When this configuration was created"
    )
    
    updated_at: Optional[str] = Field(
        None,
        description="When this configuration was last updated"
    )
    
    @field_validator('goals')
    @classmethod
    def validate_weights_sum(cls, v):
        """Ensure goal weights sum to approximately 1.0."""
        total_weight = sum(goal.weight for goal in v)
        if not (0.9 <= total_weight <= 1.1):  # Allow small rounding errors
            raise ValueError(f"Goal weights should sum to ~1.0, got {total_weight}")
        return v
    
    @field_validator('goals')
    @classmethod
    def validate_unique_goal_names(cls, v):
        """Ensure goal names are unique."""
        names = [goal.name for goal in v]
        if len(names) != len(set(names)):
            raise ValueError("Goal names must be unique")
        return v
    
    @property
    def primary_goals(self) -> List[BusinessGoal]:
        """Get primary goals (weight > 0.3)."""
        return [goal for goal in self.goals if goal.is_primary_goal]
    
    def get_goal_by_name(self, name: BusinessGoalType) -> Optional[BusinessGoal]:
        """Get a specific goal by name."""
        for goal in self.goals:
            if goal.name == name:
                return goal
        return None


# Default goal configurations for different business contexts
DEFAULT_BALANCED_GOALS = [
    BusinessGoal(
        name=BusinessGoalType.CUSTOMER_SATISFACTION,
        weight=0.35,
        description="Ensure customers are satisfied and feel heard",
        metrics=["response_time", "order_accuracy", "customer_feedback"]
    ),
    BusinessGoal(
        name=BusinessGoalType.ORDER_VALUE,
        weight=0.30,
        description="Maximize order value through intelligent suggestions",
        metrics=["average_order_value", "upsell_success_rate", "total_revenue"]
    ),
    BusinessGoal(
        name=BusinessGoalType.EFFICIENCY,
        weight=0.25,
        description="Process orders quickly and accurately",
        metrics=["processing_time", "automation_rate", "error_rate"]
    ),
    BusinessGoal(
        name=BusinessGoalType.RELATIONSHIP_BUILDING,
        weight=0.10,
        description="Build long-term customer relationships",
        metrics=["repeat_customers", "customer_lifetime_value", "referral_rate"]
    )
]

DEFAULT_REVENUE_FOCUSED_GOALS = [
    BusinessGoal(
        name=BusinessGoalType.ORDER_VALUE,
        weight=0.45,
        description="Aggressively maximize order value",
        metrics=["average_order_value", "upsell_success_rate", "margin_optimization"]
    ),
    BusinessGoal(
        name=BusinessGoalType.CUSTOMER_SATISFACTION,
        weight=0.25,
        description="Maintain customer satisfaction while increasing value",
        metrics=["order_completion_rate", "customer_retention"]
    ),
    BusinessGoal(
        name=BusinessGoalType.EFFICIENCY,
        weight=0.20,
        description="Efficient order processing",
        metrics=["processing_time", "automation_rate"]
    ),
    BusinessGoal(
        name=BusinessGoalType.RELATIONSHIP_BUILDING,
        weight=0.10,
        description="Build relationships through value delivery",
        metrics=["customer_lifetime_value", "upsell_acceptance_rate"]
    )
]

DEFAULT_SERVICE_FOCUSED_GOALS = [
    BusinessGoal(
        name=BusinessGoalType.CUSTOMER_SATISFACTION,
        weight=0.50,
        description="Prioritize exceptional customer service",
        metrics=["satisfaction_scores", "response_quality", "issue_resolution"]
    ),
    BusinessGoal(
        name=BusinessGoalType.RELATIONSHIP_BUILDING,
        weight=0.25,
        description="Build strong long-term relationships",
        metrics=["customer_retention", "relationship_strength", "trust_indicators"]
    ),
    BusinessGoal(
        name=BusinessGoalType.EFFICIENCY,
        weight=0.15,
        description="Efficient and accurate service delivery",
        metrics=["response_time", "accuracy_rate", "first_contact_resolution"]
    ),
    BusinessGoal(
        name=BusinessGoalType.ORDER_VALUE,
        weight=0.10,
        description="Natural order value through excellent service",
        metrics=["organic_upsells", "customer_suggested_additions"]
    )
]


def create_goal_configuration_from_env(distributor_id: str) -> GoalConfiguration:
    """
    Create goal configuration from environment variables.
    
    Reads goal weights from environment, allowing easy tuning without code changes.
    Falls back to balanced defaults if env vars not set.
    
    Environment variables:
    - GOAL_CUSTOMER_SATISFACTION: Weight for customer satisfaction (0.0-1.0)
    - GOAL_ORDER_VALUE: Weight for order value maximization (0.0-1.0)
    - GOAL_EFFICIENCY: Weight for processing efficiency (0.0-1.0)
    - GOAL_RELATIONSHIP_BUILDING: Weight for relationship building (0.0-1.0)
    - GOAL_CONFIDENCE_THRESHOLD: Overall confidence threshold (0.0-1.0)
    - GOAL_SCORE_THRESHOLD: Minimum action score threshold (0.0-1.0)
    
    Args:
        distributor_id: ID of the distributor
        
    Returns:
        GoalConfiguration: Configuration based on environment variables
    """
    # Read weights from environment with defaults
    satisfaction_weight = float(os.getenv('GOAL_CUSTOMER_SATISFACTION', '0.35'))
    order_value_weight = float(os.getenv('GOAL_ORDER_VALUE', '0.30'))
    efficiency_weight = float(os.getenv('GOAL_EFFICIENCY', '0.25'))
    relationship_weight = float(os.getenv('GOAL_RELATIONSHIP_BUILDING', '0.10'))
    
    # Normalize weights to sum to 1.0
    total_weight = satisfaction_weight + order_value_weight + efficiency_weight + relationship_weight
    if total_weight > 0:
        satisfaction_weight = satisfaction_weight / total_weight
        order_value_weight = order_value_weight / total_weight
        efficiency_weight = efficiency_weight / total_weight
        relationship_weight = relationship_weight / total_weight
    
    goals = [
        BusinessGoal(
            name=BusinessGoalType.CUSTOMER_SATISFACTION,
            weight=satisfaction_weight,
            description="Ensure customers are satisfied and feel heard",
            metrics=["response_time", "order_accuracy", "customer_feedback"]
        ),
        BusinessGoal(
            name=BusinessGoalType.ORDER_VALUE,
            weight=order_value_weight,
            description="Maximize order value through intelligent suggestions",
            metrics=["average_order_value", "upsell_success_rate", "total_revenue"]
        ),
        BusinessGoal(
            name=BusinessGoalType.EFFICIENCY,
            weight=efficiency_weight,
            description="Process orders quickly and accurately",
            metrics=["processing_time", "automation_rate", "error_rate"]
        ),
        BusinessGoal(
            name=BusinessGoalType.RELATIONSHIP_BUILDING,
            weight=relationship_weight,
            description="Build long-term customer relationships",
            metrics=["repeat_customers", "customer_lifetime_value", "referral_rate"]
        )
    ]
    
    # Read threshold settings
    confidence_threshold = float(os.getenv('GOAL_CONFIDENCE_THRESHOLD', '0.8'))
    score_threshold = float(os.getenv('GOAL_SCORE_THRESHOLD', '0.7'))
    
    return GoalConfiguration(
        distributor_id=distributor_id,
        goals=goals,
        confidence_threshold=confidence_threshold,
        score_threshold=score_threshold
    )


def create_default_goal_configuration(
    distributor_id: str,
    goal_type: str = "balanced"
) -> GoalConfiguration:
    """
    Create a default goal configuration for a distributor.
    
    Args:
        distributor_id: ID of the distributor
        goal_type: Type of goals ("balanced", "revenue", "service", "custom")
        
    Returns:
        GoalConfiguration: Default configuration for the specified type
        
    Raises:
        ValueError: If goal_type is not recognized
    """
    # Check for custom configuration from environment
    if goal_type == "custom" or os.getenv('USE_CUSTOM_GOALS', 'false').lower() == 'true':
        return create_goal_configuration_from_env(distributor_id)
    
    goal_map = {
        "balanced": DEFAULT_BALANCED_GOALS,
        "revenue": DEFAULT_REVENUE_FOCUSED_GOALS,
        "service": DEFAULT_SERVICE_FOCUSED_GOALS
    }
    
    if goal_type not in goal_map:
        raise ValueError(f"Unknown goal type: {goal_type}. Must be one of: {list(goal_map.keys())}, or 'custom'")
    
    return GoalConfiguration(
        distributor_id=distributor_id,
        goals=goal_map[goal_type].copy()  # Copy to avoid mutation
    )