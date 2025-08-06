"""
Agent factory for selecting between simplified autonomous and existing agents.

Simple environment variable control: USE_SIMPLIFIED_AGENT=true/false
"""

from __future__ import annotations as _annotations

import os
import logging
from typing import Union, Optional, Dict, Any
from enum import Enum

from services.database import DatabaseService
from agents.order_agent import StreamlinedOrderProcessor
from agents.simplified_autonomous_agent import SimplifiedAutonomousAgent

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents available."""
    AUTONOMOUS = "autonomous"
    STREAMLINED = "streamlined"
    FALLBACK = "fallback"


class AgentFactory:
    """
    Factory for creating and selecting appropriate order processing agents.
    
    Handles feature flag evaluation, agent instantiation, and provides
    a unified interface for order processing regardless of agent type.
    """
    
    def __init__(self, database: DatabaseService, distributor_id: str):
        """
        Initialize agent factory.
        
        Args:
            database: Database service instance
            distributor_id: Distributor ID for multi-tenant isolation
        """
        self.database = database
        self.distributor_id = distributor_id
        self._autonomous_agent = None
        self._streamlined_agent = None
        
        logger.info(f"Initialized AgentFactory for distributor {distributor_id}")
    
    async def create_agent(
        self, 
        customer_id: Optional[str] = None,
        force_agent_type: Optional[AgentType] = None
    ) -> Union[SimplifiedAutonomousAgent, StreamlinedOrderProcessor]:
        """
        Create appropriate agent based on feature flags and context.
        
        Args:
            customer_id: Customer ID for feature flag evaluation (optional)
            force_agent_type: Force specific agent type (for testing)
            
        Returns:
            Union[SimplifiedAutonomousAgent, StreamlinedOrderProcessor]: Selected agent
        """
        try:
            # Determine which agent to use
            agent_type = await self._determine_agent_type(customer_id, force_agent_type)
            
            # Create and return appropriate agent
            if agent_type == AgentType.AUTONOMOUS:
                return await self._get_autonomous_agent()
            else:
                return await self._get_streamlined_agent()
                
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            # Always fallback to streamlined agent on error
            return await self._get_streamlined_agent()
    
    async def process_message_with_best_agent(
        self, 
        message_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Process message with the most appropriate agent.
        
        Args:
            message_data: Message data from webhook
            
        Returns:
            Optional[Any]: Processing result (type depends on agent used)
        """
        customer_id = message_data.get('customer_id')
        message_id = message_data.get('id', 'unknown')
        
        try:
            # Create appropriate agent
            agent = await self.create_agent(customer_id)
            agent_type = type(agent).__name__
            
            logger.info(f"Processing message {message_id} with {agent_type}")
            
            # Process message
            result = await agent.process_message(message_data)
            
            if result:
                logger.info(f"✅ Message {message_id} processed successfully by {agent_type}")
                
                # Log agent selection for monitoring
                await self._log_agent_usage(message_id, agent_type, customer_id, True)
                
                return result
            else:
                logger.warning(f"⚠️ Message {message_id} processing returned None from {agent_type}")
                
                # If autonomous agent failed, try fallback
                fallback_enabled = os.getenv('AUTONOMOUS_FALLBACK_ENABLED', 'true').lower() in ['true', '1', 'yes']
                if isinstance(agent, SimplifiedAutonomousAgent) and fallback_enabled:
                    logger.info(f"🔄 Attempting fallback for message {message_id}")
                    fallback_agent = await self._get_streamlined_agent()
                    fallback_result = await fallback_agent.process_message(message_data)
                    
                    if fallback_result:
                        logger.info(f"✅ Fallback successful for message {message_id}")
                        await self._log_agent_usage(message_id, f"{agent_type}_fallback", customer_id, True)
                        return fallback_result
                
                await self._log_agent_usage(message_id, agent_type, customer_id, False)
                return None
                
        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}")
            
            # Emergency fallback to streamlined agent
            try:
                logger.info(f"🚨 Emergency fallback for message {message_id}")
                emergency_agent = await self._get_streamlined_agent()
                emergency_result = await emergency_agent.process_message(message_data)
                
                if emergency_result:
                    await self._log_agent_usage(message_id, "emergency_fallback", customer_id, True)
                    return emergency_result
                
            except Exception as fallback_error:
                logger.error(f"Emergency fallback also failed for message {message_id}: {fallback_error}")
            
            await self._log_agent_usage(message_id, "failed", customer_id, False)
            return None
    
    async def _determine_agent_type(
        self, 
        customer_id: Optional[str], 
        force_agent_type: Optional[AgentType]
    ) -> AgentType:
        """
        Determine which agent type to use - simple environment variable control.
        
        Args:
            customer_id: Customer ID (not used in simple mode)
            force_agent_type: Forced agent type (for testing)
            
        Returns:
            AgentType: Type of agent to use
        """
        # Handle forced agent type (for testing)
        if force_agent_type:
            logger.debug(f"Using forced agent type: {force_agent_type}")
            return force_agent_type
        
        # Simple environment variable check
        use_simplified = os.getenv('USE_SIMPLIFIED_AGENT', 'false').lower() in ['true', '1', 'yes']
        
        if use_simplified:
            logger.info(f"✅ SimplifiedAutonomousAgent SELECTED (USE_SIMPLIFIED_AGENT=true)")
            return AgentType.AUTONOMOUS
        else:
            logger.info(f"📝 StreamlinedOrderProcessor SELECTED (USE_SIMPLIFIED_AGENT=false)")
            return AgentType.STREAMLINED
    
    async def _get_autonomous_agent(self) -> SimplifiedAutonomousAgent:
        """Get or create simplified autonomous agent instance."""
        if self._autonomous_agent is None:
            logger.debug("Creating new SimplifiedAutonomousAgent instance")
            self._autonomous_agent = SimplifiedAutonomousAgent(self.database, self.distributor_id)
        return self._autonomous_agent
    
    async def _get_streamlined_agent(self) -> StreamlinedOrderProcessor:
        """Get or create streamlined agent instance."""
        if self._streamlined_agent is None:
            logger.debug("Creating new StreamlinedOrderProcessor instance")
            self._streamlined_agent = StreamlinedOrderProcessor(self.database, self.distributor_id)
        return self._streamlined_agent
    
    async def _log_agent_usage(
        self, 
        message_id: str, 
        agent_type: str, 
        customer_id: Optional[str], 
        success: bool
    ):
        """
        Log agent usage for monitoring and analytics.
        
        Args:
            message_id: Message ID
            agent_type: Type of agent used
            customer_id: Customer ID
            success: Whether processing was successful
        """
        try:
            usage_data = {
                'message_id': message_id,
                'distributor_id': self.distributor_id,
                'customer_id': customer_id,
                'agent_type': agent_type,
                'success': success,
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'environment_config': {
                    'simplified_agent_enabled': os.getenv('USE_SIMPLIFIED_AGENT', 'false'),
                    'openai_api_configured': bool(os.getenv('OPENAI_API_KEY'))
                }
            }
            
            # Store usage data (could be in a separate analytics table)
            # For now, just log it
            logger.info(f"Agent usage logged: {usage_data}")
            
            # In production, you might want to store this in a dedicated table:
            # await self.database.insert_single(
            #     table='agent_usage_logs',
            #     data=usage_data
            # )
            
        except Exception as e:
            logger.warning(f"Failed to log agent usage: {e}")
    
    def get_agent_capabilities(self, agent_type: AgentType) -> Dict[str, Any]:
        """
        Get capabilities description for an agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Dict: Agent capabilities and features
        """
        capabilities = {
            AgentType.AUTONOMOUS: {
                "name": "Autonomous Order Agent",
                "description": "AI agent with goal-oriented decision making",
                "features": [
                    "Goal-based action evaluation",
                    "Customer preference learning",
                    "Autonomous order creation",
                    "Intelligent clarification requests",
                    "Product suggestions",
                    "Context-aware decisions"
                ],
                "confidence_thresholds": {
                    "order_creation": 0.85,
                    "product_suggestions": 0.7,
                    "clarification": 0.6
                }
            },
            AgentType.STREAMLINED: {
                "name": "Streamlined Order Processor",
                "description": "Reliable rule-based order processing",
                "features": [
                    "Intent classification",
                    "Product extraction",
                    "Catalog matching",
                    "Order creation",
                    "Basic clarification"
                ],
                "confidence_thresholds": {
                    "order_creation": 0.8,
                    "processing": 0.6
                }
            }
        }
        
        return capabilities.get(agent_type, {})
    
    async def get_agent_health_status(self) -> Dict[str, Any]:
        """
        Get health status of agent factory and available agents.
        
        Returns:
            Dict: Health status information
        """
        try:
            status = {
                "factory_status": "healthy",
                "distributor_id": self.distributor_id,
                "configuration": {
                    "simplified_agent_enabled": os.getenv('USE_SIMPLIFIED_AGENT', 'false'),
                    "openai_api_key_configured": bool(os.getenv('OPENAI_API_KEY')),
                    "supabase_configured": bool(os.getenv('NEXT_PUBLIC_SUPABASE_URL'))
                },
                "agents": {
                    "autonomous": {
                        "available": True,
                        "initialized": self._autonomous_agent is not None
                    },
                    "streamlined": {
                        "available": True,
                        "initialized": self._streamlined_agent is not None
                    }
                },
                "database_status": "connected" if self.database else "disconnected"
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get agent health status: {e}")
            return {
                "factory_status": "error",
                "error": str(e),
                "distributor_id": self.distributor_id
            }
    
    def reset_agents(self):
        """Reset agent instances (useful for testing or configuration changes)."""
        logger.info("Resetting agent instances")
        self._autonomous_agent = None
        self._streamlined_agent = None


def create_agent_factory(database: DatabaseService, distributor_id: str) -> AgentFactory:
    """
    Factory function to create agent factory.
    
    Args:
        database: Database service instance
        distributor_id: Distributor ID
        
    Returns:
        AgentFactory: Configured agent factory
    """
    return AgentFactory(database, distributor_id)


# Convenience functions for direct agent creation
async def create_best_agent(
    database: DatabaseService, 
    distributor_id: str, 
    customer_id: Optional[str] = None
) -> Union[SimplifiedAutonomousAgent, StreamlinedOrderProcessor]:
    """
    Create the best available agent for the given context.
    
    Args:
        database: Database service instance
        distributor_id: Distributor ID
        customer_id: Customer ID (optional)
        
    Returns:
        Union[SimplifiedAutonomousAgent, StreamlinedOrderProcessor]: Best available agent
    """
    factory = create_agent_factory(database, distributor_id)
    return await factory.create_agent(customer_id)


async def process_message_intelligently(
    database: DatabaseService,
    distributor_id: str,
    message_data: Dict[str, Any]
) -> Optional[Any]:
    """
    Process message with intelligent agent selection.
    
    Args:
        database: Database service instance
        distributor_id: Distributor ID
        message_data: Message data
        
    Returns:
        Optional[Any]: Processing result
    """
    factory = create_agent_factory(database, distributor_id)
    return await factory.process_message_with_best_agent(message_data)