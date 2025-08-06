"""
Feature flag configuration for autonomous agent deployment.

Provides safe deployment capabilities with percentage-based rollout,
fallback mechanisms, and environment variable management.
"""

from __future__ import annotations as _annotations

import os
import logging
import hashlib
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class FeatureFlagStatus(str, Enum):
    """Status options for feature flags."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    TESTING = "testing"
    GRADUAL_ROLLOUT = "gradual_rollout"


class AutonomousAgentFeature(str, Enum):
    """Specific autonomous agent features that can be toggled."""
    AUTONOMOUS_AGENT_ENABLED = "autonomous_agent_enabled"
    GOAL_EVALUATION_ENABLED = "goal_evaluation_enabled"
    MEMORY_LEARNING_ENABLED = "memory_learning_enabled"
    AUTONOMOUS_ORDER_CREATION = "autonomous_order_creation"
    PRODUCT_SUGGESTIONS = "product_suggestions"
    CLARIFICATION_REQUESTS = "clarification_requests"
    PREFERENCE_LEARNING = "preference_learning"
    FALLBACK_TO_EXISTING = "fallback_to_existing"


class FeatureFlag(BaseModel):
    """Individual feature flag configuration."""
    
    name: str = Field(
        ...,
        description="Name of the feature flag"
    )
    
    status: FeatureFlagStatus = Field(
        default=FeatureFlagStatus.DISABLED,
        description="Current status of the feature"
    )
    
    rollout_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of users to receive this feature (0-100)"
    )
    
    description: str = Field(
        ...,
        description="Description of what this feature does"
    )
    
    enabled_for_distributors: List[str] = Field(
        default_factory=list,
        description="Specific distributor IDs that always get this feature"
    )
    
    disabled_for_distributors: List[str] = Field(
        default_factory=list,
        description="Specific distributor IDs that never get this feature"
    )
    
    minimum_confidence_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for this feature"
    )
    
    dependencies: List[str] = Field(
        default_factory=list,
        description="Other features this feature depends on"
    )
    
    created_at: Optional[str] = Field(
        None,
        description="When this flag was created"
    )
    
    updated_at: Optional[str] = Field(
        None,
        description="When this flag was last updated"
    )
    
    @field_validator('rollout_percentage')
    @classmethod
    def validate_rollout_percentage(cls, v):
        """Validate rollout percentage based on status."""
        # Note: In Pydantic v2, we can't access other field values in field_validator
        # This validation will be moved to model_validator if needed
        return v


class FeatureFlagConfiguration(BaseModel):
    """Complete feature flag configuration for autonomous agent."""
    
    flags: Dict[str, FeatureFlag] = Field(
        default_factory=dict,
        description="Dictionary of feature flags by name"
    )
    
    global_autonomous_enabled: bool = Field(
        default=False,
        description="Global switch for autonomous agent functionality"
    )
    
    fallback_enabled: bool = Field(
        default=True,
        description="Whether to fallback to existing agent when autonomous fails"
    )
    
    testing_mode: bool = Field(
        default=False,
        description="Whether the system is in testing mode"
    )
    
    distributor_overrides: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-distributor feature overrides"
    )
    
    def is_feature_enabled(
        self,
        feature_name: str,
        distributor_id: str,
        customer_id: Optional[str] = None
    ) -> bool:
        """
        Check if a feature is enabled for a specific distributor/customer.
        
        Args:
            feature_name: Name of the feature to check
            distributor_id: Distributor ID
            customer_id: Customer ID (for percentage-based rollout)
            
        Returns:
            bool: True if feature is enabled
        """
        # Check global autonomous switch first
        if not self.global_autonomous_enabled and feature_name != AutonomousAgentFeature.FALLBACK_TO_EXISTING:
            return False
        
        # Check if feature exists
        if feature_name not in self.flags:
            logger.warning(f"Unknown feature flag: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        
        # Check explicit distributor overrides first
        if distributor_id in self.distributor_overrides:
            override = self.distributor_overrides[distributor_id].get(feature_name)
            if override is not None:
                return bool(override)
        
        # Check explicit enable/disable lists
        if distributor_id in flag.disabled_for_distributors:
            return False
        
        if distributor_id in flag.enabled_for_distributors:
            return True
        
        # Check feature status
        if flag.status == FeatureFlagStatus.DISABLED:
            return False
        
        if flag.status == FeatureFlagStatus.ENABLED:
            return True
        
        if flag.status in [FeatureFlagStatus.TESTING, FeatureFlagStatus.GRADUAL_ROLLOUT]:
            # Use percentage-based rollout
            return self._calculate_rollout_eligibility(
                feature_name, distributor_id, customer_id, flag.rollout_percentage
            )
        
        return False
    
    def check_dependencies(
        self,
        feature_name: str,
        distributor_id: str,
        customer_id: Optional[str] = None
    ) -> bool:
        """
        Check if all dependencies for a feature are met.
        
        Args:
            feature_name: Name of the feature to check
            distributor_id: Distributor ID
            customer_id: Customer ID
            
        Returns:
            bool: True if all dependencies are satisfied
        """
        if feature_name not in self.flags:
            return False
        
        flag = self.flags[feature_name]
        
        # Check all dependencies
        for dependency in flag.dependencies:
            if not self.is_feature_enabled(dependency, distributor_id, customer_id):
                logger.debug(f"Feature {feature_name} disabled due to unmet dependency: {dependency}")
                return False
        
        return True
    
    def get_confidence_threshold(self, feature_name: str) -> float:
        """Get confidence threshold for a feature."""
        if feature_name in self.flags:
            return self.flags[feature_name].minimum_confidence_threshold or 0.8
        return 0.8
    
    def _calculate_rollout_eligibility(
        self,
        feature_name: str,
        distributor_id: str,
        customer_id: Optional[str],
        rollout_percentage: float
    ) -> bool:
        """
        Calculate if user is eligible for rollout based on percentage.
        
        Uses deterministic hash-based approach for consistent rollout.
        """
        if rollout_percentage <= 0:
            return False
        
        if rollout_percentage >= 100:
            return True
        
        # Create deterministic hash based on feature, distributor, and customer
        hash_input = f"{feature_name}:{distributor_id}"
        if customer_id:
            hash_input += f":{customer_id}"
        
        # Use hash to determine eligibility (ensures consistency)
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        user_percentage = (hash_value % 10000) / 100.0  # Convert to 0-100 range
        
        eligible = user_percentage < rollout_percentage
        logger.debug(f"Rollout calculation for {feature_name}: {user_percentage:.2f}% < {rollout_percentage}% = {eligible}")
        
        return eligible


def create_default_feature_flags() -> FeatureFlagConfiguration:
    """
    Create default feature flag configuration.
    
    Returns:
        FeatureFlagConfiguration: Default configuration with all features disabled
    """
    flags = {}
    
    # Main autonomous agent flag
    flags[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED] = FeatureFlag(
        name=AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
        status=FeatureFlagStatus.DISABLED,
        rollout_percentage=0.0,
        description="Master switch for autonomous agent functionality",
        dependencies=[]
    )
    
    # Goal evaluation system
    flags[AutonomousAgentFeature.GOAL_EVALUATION_ENABLED] = FeatureFlag(
        name=AutonomousAgentFeature.GOAL_EVALUATION_ENABLED,
        status=FeatureFlagStatus.DISABLED,
        rollout_percentage=0.0,
        description="Enable goal-oriented decision making",
        dependencies=[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED]
    )
    
    # Memory and learning system
    flags[AutonomousAgentFeature.MEMORY_LEARNING_ENABLED] = FeatureFlag(
        name=AutonomousAgentFeature.MEMORY_LEARNING_ENABLED,
        status=FeatureFlagStatus.DISABLED,
        rollout_percentage=0.0,
        description="Enable customer preference learning and memory",
        dependencies=[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED]
    )
    
    # Autonomous order creation
    flags[AutonomousAgentFeature.AUTONOMOUS_ORDER_CREATION] = FeatureFlag(
        name=AutonomousAgentFeature.AUTONOMOUS_ORDER_CREATION,
        status=FeatureFlagStatus.DISABLED,
        rollout_percentage=0.0,
        description="Allow autonomous agent to create orders",
        dependencies=[
            AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
            AutonomousAgentFeature.GOAL_EVALUATION_ENABLED
        ],
        minimum_confidence_threshold=float(os.getenv('AUTONOMOUS_ORDER_CONFIDENCE', '0.85'))
    )
    
    # Product suggestions
    flags[AutonomousAgentFeature.PRODUCT_SUGGESTIONS] = FeatureFlag(
        name=AutonomousAgentFeature.PRODUCT_SUGGESTIONS,
        status=FeatureFlagStatus.DISABLED,
        rollout_percentage=0.0,
        description="Enable autonomous product suggestions",
        dependencies=[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED],
        minimum_confidence_threshold=float(os.getenv('AUTONOMOUS_SUGGESTION_CONFIDENCE', '0.7'))
    )
    
    # Clarification requests
    flags[AutonomousAgentFeature.CLARIFICATION_REQUESTS] = FeatureFlag(
        name=AutonomousAgentFeature.CLARIFICATION_REQUESTS,
        status=FeatureFlagStatus.DISABLED,
        rollout_percentage=0.0,
        description="Enable autonomous clarification requests",
        dependencies=[AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED],
        minimum_confidence_threshold=float(os.getenv('AUTONOMOUS_CLARIFICATION_CONFIDENCE', '0.6'))
    )
    
    # Preference learning
    flags[AutonomousAgentFeature.PREFERENCE_LEARNING] = FeatureFlag(
        name=AutonomousAgentFeature.PREFERENCE_LEARNING,
        status=FeatureFlagStatus.DISABLED,
        rollout_percentage=0.0,
        description="Enable autonomous customer preference learning",
        dependencies=[
            AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
            AutonomousAgentFeature.MEMORY_LEARNING_ENABLED
        ]
    )
    
    # Fallback mechanism (should usually be enabled)
    flags[AutonomousAgentFeature.FALLBACK_TO_EXISTING] = FeatureFlag(
        name=AutonomousAgentFeature.FALLBACK_TO_EXISTING,
        status=FeatureFlagStatus.ENABLED,
        rollout_percentage=100.0,
        description="Fallback to existing agent when autonomous agent fails",
        dependencies=[]
    )
    
    return FeatureFlagConfiguration(
        flags=flags,
        global_autonomous_enabled=False,
        fallback_enabled=True,
        testing_mode=False
    )


def load_feature_flags_from_env() -> FeatureFlagConfiguration:
    """
    Load feature flag configuration from environment variables.
    
    Returns:
        FeatureFlagConfiguration: Configuration based on environment variables
    """
    # Start with default configuration
    config = create_default_feature_flags()
    
    # Log environment variable values for debugging
    logger.info(f"🔧 Loading feature flags from environment...")
    logger.info(f"🔧 USE_AUTONOMOUS_AGENT = {os.environ.get('USE_AUTONOMOUS_AGENT', 'NOT SET')}")
    logger.info(f"🔧 AUTONOMOUS_FALLBACK_ENABLED = {os.environ.get('AUTONOMOUS_FALLBACK_ENABLED', 'NOT SET')}")
    logger.info(f"🔧 AUTONOMOUS_TESTING_MODE = {os.environ.get('AUTONOMOUS_TESTING_MODE', 'NOT SET')}")
    
    # Update based on environment variables
    config.global_autonomous_enabled = _parse_bool_env(
        'USE_AUTONOMOUS_AGENT', 
        config.global_autonomous_enabled
    )
    
    config.fallback_enabled = _parse_bool_env(
        'AUTONOMOUS_FALLBACK_ENABLED', 
        config.fallback_enabled
    )
    
    config.testing_mode = _parse_bool_env(
        'AUTONOMOUS_TESTING_MODE', 
        config.testing_mode
    )
    
    # Update individual feature flags from environment
    for feature_name in AutonomousAgentFeature:
        env_var_name = f"AUTONOMOUS_{feature_name.upper()}"
        
        # Check if feature is enabled via environment
        if env_var_name in os.environ:
            is_enabled = _parse_bool_env(env_var_name, False)
            logger.info(f"🔧 {env_var_name} = {os.environ[env_var_name]} (parsed: {is_enabled})")
            if feature_name in config.flags:
                if is_enabled:
                    config.flags[feature_name].status = FeatureFlagStatus.ENABLED
                    config.flags[feature_name].rollout_percentage = 100.0
                else:
                    config.flags[feature_name].status = FeatureFlagStatus.DISABLED
                    config.flags[feature_name].rollout_percentage = 0.0
        
        # Check for rollout percentage
        rollout_env_var = f"AUTONOMOUS_{feature_name.upper()}_PERCENTAGE"
        if rollout_env_var in os.environ:
            try:
                percentage = float(os.environ[rollout_env_var])
                if 0 <= percentage <= 100 and feature_name in config.flags:
                    config.flags[feature_name].rollout_percentage = percentage
                    if percentage > 0:
                        config.flags[feature_name].status = FeatureFlagStatus.GRADUAL_ROLLOUT
                    else:
                        config.flags[feature_name].status = FeatureFlagStatus.DISABLED
            except ValueError:
                logger.warning(f"Invalid percentage value for {rollout_env_var}")
    
    logger.info(f"✅ Feature flags loaded: autonomous={config.global_autonomous_enabled}, "
               f"fallback={config.fallback_enabled}, testing={config.testing_mode}")
    
    # Log status of key features
    autonomous_flag = config.flags.get(AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED)
    if autonomous_flag:
        logger.info(f"✅ Autonomous agent feature: status={autonomous_flag.status}, rollout={autonomous_flag.rollout_percentage}%")
    
    return config


def _parse_bool_env(env_var: str, default: bool) -> bool:
    """Parse boolean environment variable."""
    value = os.environ.get(env_var, '').lower()
    if value in ['true', '1', 'yes', 'on', 'enabled']:
        return True
    elif value in ['false', '0', 'no', 'off', 'disabled']:
        return False
    else:
        return default


# Global feature flags instance
feature_flags = load_feature_flags_from_env()


def is_autonomous_agent_enabled(distributor_id: str, customer_id: Optional[str] = None) -> bool:
    """
    Quick check if autonomous agent is enabled for a distributor/customer.
    
    Args:
        distributor_id: Distributor ID
        customer_id: Customer ID (optional)
        
    Returns:
        bool: True if autonomous agent should be used
    """
    return feature_flags.is_feature_enabled(
        AutonomousAgentFeature.AUTONOMOUS_AGENT_ENABLED,
        distributor_id,
        customer_id
    )


def should_fallback_to_existing(distributor_id: str, customer_id: Optional[str] = None) -> bool:
    """
    Check if should fallback to existing agent.
    
    Args:
        distributor_id: Distributor ID
        customer_id: Customer ID (optional)
        
    Returns:
        bool: True if should fallback to existing agent
    """
    return feature_flags.is_feature_enabled(
        AutonomousAgentFeature.FALLBACK_TO_EXISTING,
        distributor_id,
        customer_id
    )


def get_autonomous_confidence_threshold(feature_name: str) -> float:
    """
    Get confidence threshold for autonomous action.
    
    Args:
        feature_name: Name of the feature
        
    Returns:
        float: Confidence threshold
    """
    return feature_flags.get_confidence_threshold(feature_name)