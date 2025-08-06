"""
Goal evaluation service for autonomous decision making.

Evaluates actions against business goals with deterministic scoring algorithms
to enable explainable AI decisions.
"""

from __future__ import annotations as _annotations

import logging
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from schemas.goals import BusinessGoal, ActionEvaluation, BusinessGoalType
from schemas.autonomous_agent import (
    AutonomousAction, AutonomousActionType, AutonomousAgentContext
)

logger = logging.getLogger(__name__)


class GoalEvaluator:
    """
    Service for evaluating autonomous actions against business goals.
    
    Uses deterministic algorithms to score actions, ensuring consistent
    and explainable decision making.
    """
    
    def __init__(self):
        """Initialize the goal evaluator."""
        logger.info("Initialized GoalEvaluator for autonomous decision making")
    
    async def evaluate_action(
        self, 
        action: AutonomousAction,
        context: AutonomousAgentContext,
        goals: List[BusinessGoal]
    ) -> ActionEvaluation:
        """
        Evaluate an action against all business goals.
        
        Args:
            action: Action to evaluate
            context: Current context for evaluation
            goals: List of business goals with weights
            
        Returns:
            ActionEvaluation: Complete evaluation with scores and reasoning
        """
        try:
            logger.debug(f"Evaluating action {action.action_type} against {len(goals)} business goals")
            
            goal_scores = {}
            detailed_reasoning = []
            
            # Score action against each business goal
            for goal in goals:
                score = await self._score_action_for_goal(action, goal, context)
                goal_scores[goal.name] = score
                
                # Add reasoning for this goal
                goal_reasoning = await self._explain_goal_score(action, goal, context, score)
                detailed_reasoning.append(f"{goal.name}: {score:.2f} - {goal_reasoning}")
                
                logger.debug(f"Goal {goal.name}: score={score:.3f}, weight={goal.weight}")
            
            # Calculate weighted overall score
            overall_score = sum(
                goal_scores[goal.name] * goal.weight 
                for goal in goals
            )
            
            # Calculate confidence based on score consistency and context
            confidence = await self._calculate_confidence(goal_scores, context, action)
            
            # Generate comprehensive reasoning
            reasoning = await self._generate_comprehensive_reasoning(
                action, goal_scores, goals, detailed_reasoning, overall_score, confidence
            )
            
            evaluation = ActionEvaluation(
                action_name=action.action_type,
                goal_scores=goal_scores,
                overall_score=round(overall_score, 3),
                reasoning=reasoning,
                confidence=round(confidence, 3),
                metadata={
                    "evaluation_timestamp": datetime.now().isoformat(),
                    "context_factors": await self._extract_context_factors(context),
                    "action_confidence": action.confidence,
                    "goal_weights": {goal.name: goal.weight for goal in goals}
                }
            )
            
            logger.info(f"Action {action.action_type} evaluated: score={overall_score:.3f}, confidence={confidence:.3f}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate action {action.action_type}: {e}")
            # Return safe fallback evaluation
            return ActionEvaluation(
                action_name=action.action_type,
                goal_scores={goal.name: 0.5 for goal in goals},
                overall_score=0.5,
                reasoning=f"Evaluation failed: {str(e)}. Using fallback scoring.",
                confidence=0.3,
                metadata={"error": str(e)}
            )
    
    async def _score_action_for_goal(
        self, 
        action: AutonomousAction, 
        goal: BusinessGoal, 
        context: AutonomousAgentContext
    ) -> float:
        """
        Score a specific action against a single business goal.
        
        Args:
            action: Action to score
            goal: Business goal to score against
            context: Context for scoring
            
        Returns:
            float: Score between 0.0 and 1.0
        """
        try:
            # Route to specific scoring algorithm based on goal type
            if goal.name == BusinessGoalType.CUSTOMER_SATISFACTION:
                return await self._score_customer_satisfaction(action, context)
            elif goal.name == BusinessGoalType.ORDER_VALUE:
                return await self._score_order_value(action, context)
            elif goal.name == BusinessGoalType.EFFICIENCY:
                return await self._score_efficiency(action, context)
            elif goal.name == BusinessGoalType.RELATIONSHIP_BUILDING:
                return await self._score_relationship_building(action, context)
            else:
                logger.warning(f"Unknown goal type: {goal.name}, using default scoring")
                return 0.5  # Default neutral score
                
        except Exception as e:
            logger.error(f"Failed to score action for goal {goal.name}: {e}")
            return 0.3  # Conservative fallback score
    
    async def _score_customer_satisfaction(
        self, action: AutonomousAction, context: AutonomousAgentContext
    ) -> float:
        """Score action for customer satisfaction goal."""
        base_score = 0.5
        
        # Bonus for actions that directly help customers
        if action.action_type == AutonomousActionType.CREATE_ORDER:
            if context.has_buy_intent and context.has_extracted_products:
                base_score = 0.9  # Customer wants to buy and we're fulfilling
            else:
                base_score = 0.3  # Creating order without clear intent is bad
        
        elif action.action_type == AutonomousActionType.ASK_CLARIFICATION:
            base_score = 0.7  # Asking for clarity is generally good
            
        elif action.action_type == AutonomousActionType.PROVIDE_INFORMATION:
            base_score = 0.8  # Providing info is customer-friendly
            
        elif action.action_type == AutonomousActionType.SUGGEST_PRODUCTS:
            base_score = 0.7  # Suggestions can be helpful
            
        elif action.action_type == AutonomousActionType.ESCALATE_TO_HUMAN:
            base_score = 0.6  # Sometimes necessary but not ideal
        
        # Adjust based on context factors
        if context.time_context.business_hours:
            base_score += 0.05  # Better to help during business hours
        
        if context.customer_order_history_length > 0:
            base_score += 0.05  # Existing customers get slight preference
        
        # Penalize if action confidence is low
        if action.confidence < 0.6:
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _score_order_value(
        self, action: AutonomousAction, context: AutonomousAgentContext
    ) -> float:
        """Score action for order value maximization goal."""
        base_score = 0.5
        
        if action.action_type == AutonomousActionType.CREATE_ORDER:
            # High score if creating order with multiple products
            num_products = len(context.extracted_products)
            if num_products == 0:
                base_score = 0.2  # No products = poor order value
            elif num_products == 1:
                base_score = 0.6  # Single product is okay
            elif num_products >= 2:
                base_score = 0.9  # Multiple products = good order value
                
            # Bonus for high quantities
            total_quantity = sum(p.quantity for p in context.extracted_products)
            if total_quantity > 5:
                base_score = min(1.0, base_score + 0.1)
        
        elif action.action_type == AutonomousActionType.SUGGEST_PRODUCTS:
            base_score = 0.8  # Suggestions can increase order value
            
        elif action.action_type == AutonomousActionType.ASK_CLARIFICATION:
            base_score = 0.4  # Clarification doesn't directly increase value
            
        elif action.action_type == AutonomousActionType.PROVIDE_INFORMATION:
            base_score = 0.3  # Info doesn't directly increase value
        
        # Adjust based on customer history
        if context.recent_orders:
            # Existing customers are more likely to place larger orders
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _score_efficiency(
        self, action: AutonomousAction, context: AutonomousAgentContext
    ) -> float:
        """Score action for operational efficiency goal."""
        base_score = 0.5
        
        if action.action_type == AutonomousActionType.CREATE_ORDER:
            if context.has_buy_intent and action.confidence >= 0.8:
                base_score = 0.95  # Direct order creation is very efficient
            else:
                base_score = 0.4  # Low confidence orders are inefficient
        
        elif action.action_type == AutonomousActionType.ESCALATE_TO_HUMAN:
            base_score = 0.2  # Human escalation is inefficient
            
        elif action.action_type == AutonomousActionType.ASK_CLARIFICATION:
            base_score = 0.6  # Clarification prevents errors but takes time
            
        elif action.action_type == AutonomousActionType.PROVIDE_INFORMATION:
            base_score = 0.7  # Info provision is reasonably efficient
        
        # Bonus for high confidence actions
        if action.confidence >= 0.9:
            base_score += 0.1
        elif action.confidence < 0.6:
            base_score -= 0.15
        
        # Penalty for complex actions during peak hours
        if context.time_context.peak_hours and action.requires_customer_response:
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _score_relationship_building(
        self, action: AutonomousAction, context: AutonomousAgentContext
    ) -> float:
        """Score action for long-term relationship building goal."""
        base_score = 0.5
        
        if action.action_type == AutonomousActionType.CREATE_ORDER:
            # Good orders build relationships
            if action.confidence >= 0.8:
                base_score = 0.8
            else:
                base_score = 0.4  # Poor orders damage relationships
        
        elif action.action_type == AutonomousActionType.ASK_CLARIFICATION:
            base_score = 0.9  # Clarification shows care and attention
            
        elif action.action_type == AutonomousActionType.PROVIDE_INFORMATION:
            base_score = 0.85  # Helpful information builds trust
            
        elif action.action_type == AutonomousActionType.SUGGEST_PRODUCTS:
            base_score = 0.7  # Good suggestions build relationships
            
        elif action.action_type == AutonomousActionType.UPDATE_CUSTOMER_PREFERENCES:
            base_score = 0.95  # Learning preferences is excellent for relationships
        
        # Bonus for personalized interactions
        if len(context.customer_preferences) > 0:
            base_score += 0.05  # Using known preferences
        
        # Bonus for repeat customers
        if context.customer_order_history_length >= 3:
            base_score += 0.05  # Loyal customers get special attention
        
        return max(0.0, min(1.0, base_score))
    
    async def _calculate_confidence(
        self, 
        goal_scores: Dict[str, float], 
        context: AutonomousAgentContext, 
        action: AutonomousAction
    ) -> float:
        """Calculate confidence in the evaluation."""
        base_confidence = 0.7
        
        # Higher confidence if goal scores are consistent
        scores = list(goal_scores.values())
        if scores:
            score_variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
            consistency_bonus = max(0, 0.2 - score_variance)  # Less variance = more confidence
            base_confidence += consistency_bonus
        
        # Higher confidence for actions with good intrinsic confidence
        base_confidence += (action.confidence - 0.5) * 0.3
        
        # Higher confidence with more context
        context_factors = 0
        if context.has_buy_intent:
            context_factors += 1
        if context.has_extracted_products:
            context_factors += 1
        if context.customer_order_history_length > 0:
            context_factors += 1
        if len(context.customer_preferences) > 0:
            context_factors += 1
        
        context_bonus = min(0.2, context_factors * 0.05)
        base_confidence += context_bonus
        
        # Lower confidence during complex scenarios
        if context.time_context.peak_hours:
            base_confidence -= 0.05
        
        return max(0.0, min(1.0, base_confidence))
    
    async def _explain_goal_score(
        self, action: AutonomousAction, goal: BusinessGoal, 
        context: AutonomousAgentContext, score: float
    ) -> str:
        """Generate explanation for a specific goal score."""
        explanations = {
            BusinessGoalType.CUSTOMER_SATISFACTION: self._explain_satisfaction_score,
            BusinessGoalType.ORDER_VALUE: self._explain_order_value_score,
            BusinessGoalType.EFFICIENCY: self._explain_efficiency_score,
            BusinessGoalType.RELATIONSHIP_BUILDING: self._explain_relationship_score
        }
        
        if goal.name in explanations:
            return await explanations[goal.name](action, context, score)
        else:
            return f"Score {score:.2f} based on general action evaluation"
    
    async def _explain_satisfaction_score(
        self, action: AutonomousAction, context: AutonomousAgentContext, score: float
    ) -> str:
        """Explain customer satisfaction score."""
        if score >= 0.8:
            return "Action directly fulfills customer needs with high confidence"
        elif score >= 0.6:
            return "Action is helpful but may require customer interaction"
        elif score >= 0.4:
            return "Action provides some value but has limitations"
        else:
            return "Action may not effectively address customer needs"
    
    async def _explain_order_value_score(
        self, action: AutonomousAction, context: AutonomousAgentContext, score: float
    ) -> str:
        """Explain order value score."""
        if action.action_type == AutonomousActionType.CREATE_ORDER:
            num_products = len(context.extracted_products)
            if score >= 0.8:
                return f"Creates order with {num_products} products, maximizing value"
            else:
                return f"Order creation with limited products ({num_products})"
        elif action.action_type == AutonomousActionType.SUGGEST_PRODUCTS:
            return "Product suggestions can increase order value"
        else:
            return "Action doesn't directly impact order value"
    
    async def _explain_efficiency_score(
        self, action: AutonomousAction, context: AutonomousAgentContext, score: float
    ) -> str:
        """Explain efficiency score."""
        if action.action_type == AutonomousActionType.CREATE_ORDER and score >= 0.8:
            return "Direct order creation with high confidence maximizes efficiency"
        elif action.action_type == AutonomousActionType.ESCALATE_TO_HUMAN:
            return "Human escalation reduces automation efficiency"
        elif action.requires_customer_response:
            return "Action requires customer interaction, reducing immediate efficiency"
        else:
            return f"Action confidence {action.confidence:.2f} affects efficiency score"
    
    async def _explain_relationship_score(
        self, action: AutonomousAction, context: AutonomousAgentContext, score: float
    ) -> str:
        """Explain relationship building score."""
        if action.action_type == AutonomousActionType.ASK_CLARIFICATION:
            return "Asking for clarification shows care and attention to detail"
        elif action.action_type == AutonomousActionType.PROVIDE_INFORMATION:
            return "Providing helpful information builds trust and relationship"
        elif action.action_type == AutonomousActionType.CREATE_ORDER and score >= 0.7:
            return "Successful order fulfillment strengthens customer relationship"
        else:
            return f"Action contributes moderately to relationship building"
    
    async def _generate_comprehensive_reasoning(
        self, 
        action: AutonomousAction,
        goal_scores: Dict[str, float],
        goals: List[BusinessGoal],
        detailed_reasoning: List[str],
        overall_score: float,
        confidence: float
    ) -> str:
        """Generate comprehensive reasoning for the evaluation."""
        reasoning_parts = [
            f"Action: {action.action_type}",
            f"Overall Score: {overall_score:.3f} (confidence: {confidence:.3f})",
            "",
            "Goal Breakdown:"
        ]
        
        # Add detailed goal reasoning
        reasoning_parts.extend([f"• {reason}" for reason in detailed_reasoning])
        
        # Add summary
        reasoning_parts.extend([
            "",
            "Summary:"
        ])
        
        if overall_score >= 0.8:
            reasoning_parts.append("• Highly recommended action with strong goal alignment")
        elif overall_score >= 0.6:
            reasoning_parts.append("• Moderately good action with acceptable trade-offs")
        elif overall_score >= 0.4:
            reasoning_parts.append("• Marginal action with mixed goal performance")
        else:
            reasoning_parts.append("• Poor action that conflicts with multiple goals")
        
        if confidence >= 0.8:
            reasoning_parts.append("• High confidence in evaluation accuracy")
        elif confidence >= 0.6:
            reasoning_parts.append("• Moderate confidence, some uncertainty factors present")
        else:
            reasoning_parts.append("• Low confidence, significant uncertainty in evaluation")
        
        return "\n".join(reasoning_parts)
    
    async def _extract_context_factors(self, context: AutonomousAgentContext) -> List[str]:
        """Extract key context factors for metadata."""
        factors = []
        
        if context.has_buy_intent:
            factors.append("buy_intent_detected")
        
        if context.has_extracted_products:
            factors.append(f"products_extracted:{len(context.extracted_products)}")
        
        if context.customer_order_history_length > 0:
            factors.append(f"order_history:{context.customer_order_history_length}")
        
        if len(context.customer_preferences) > 0:
            factors.append(f"known_preferences:{len(context.customer_preferences)}")
        
        if context.time_context.business_hours:
            factors.append("business_hours")
        
        if context.time_context.peak_hours:
            factors.append("peak_hours")
        
        return factors


def create_goal_evaluator() -> GoalEvaluator:
    """
    Factory function to create a goal evaluator.
    
    Returns:
        GoalEvaluator: Configured goal evaluator instance
    """
    return GoalEvaluator()