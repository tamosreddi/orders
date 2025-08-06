"""
Autonomous actions tools for goal-oriented decision making.

Implements all actions the autonomous agent can take, following existing
tool patterns from supabase_tools.py with proper Pydantic AI decorators.
"""

from __future__ import annotations as _annotations

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from schemas.autonomous_agent import (
    AutonomousAction, AutonomousActionType, AutonomousAgentContext,
    CustomerPreference, LearningEvent
)
from schemas.order import OrderCreation, OrderProduct
from schemas.message import ExtractedProduct
from tools.supabase_tools import (
    create_order, create_distributor_message, fetch_product_catalog
)

logger = logging.getLogger(__name__)


class CreateOrderAction(BaseModel):
    """Parameters for creating an order autonomously."""
    
    products: List[Dict[str, Any]] = Field(
        ...,
        description="List of products to include in the order"
    )
    
    customer_notes: Optional[str] = Field(
        None,
        description="Additional customer notes or comments"
    )
    
    delivery_date: Optional[str] = Field(
        None,
        description="Requested delivery date if specified"
    )
    
    confidence_override: Optional[float] = Field(
        None,
        description="Override confidence level for this order"
    )


class AskClarificationAction(BaseModel):
    """Parameters for asking customer clarification."""
    
    question: str = Field(
        ...,
        min_length=1,
        description="Clarifying question to ask the customer"
    )
    
    question_type: str = Field(
        default="product_clarification",
        description="Type of clarification being requested"
    )
    
    context_summary: Optional[str] = Field(
        None,
        description="Summary of why clarification is needed"
    )


class SuggestProductsAction(BaseModel):
    """Parameters for suggesting products to customer."""
    
    suggested_products: List[Dict[str, Any]] = Field(
        ...,
        description="List of products to suggest"
    )
    
    suggestion_reason: str = Field(
        ...,
        description="Reason for these suggestions"
    )
    
    include_pricing: bool = Field(
        default=True,
        description="Whether to include pricing in suggestions"
    )


class ProvideInformationAction(BaseModel):
    """Parameters for providing information to customer."""
    
    information_type: str = Field(
        ...,
        description="Type of information being provided"
    )
    
    content: str = Field(
        ...,
        min_length=1,
        description="Information content to provide"
    )
    
    include_next_steps: bool = Field(
        default=True,
        description="Whether to include suggested next steps"
    )


class UpdatePreferencesAction(BaseModel):
    """Parameters for updating customer preferences."""
    
    preferences: List[Dict[str, Any]] = Field(
        ...,
        description="Preferences to learn or update"
    )
    
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in these preferences"
    )


class ProvidePricingAction(BaseModel):
    """Parameters for providing product pricing."""
    
    query_type: str = Field(
        default="pricing",
        description="Type of pricing query"
    )
    
    message_content: str = Field(
        ...,
        description="Original customer message asking for pricing"
    )
    
    specific_products: Optional[List[str]] = Field(
        None,
        description="Specific products mentioned if any"
    )


class CheckAvailabilityAction(BaseModel):
    """Parameters for checking product availability."""
    
    query_type: str = Field(
        default="availability",
        description="Type of availability query"
    )
    
    message_content: str = Field(
        ...,
        description="Original customer message asking about availability"
    )
    
    specific_products: Optional[List[str]] = Field(
        None,
        description="Specific products mentioned if any"
    )


async def execute_create_order_action(
    action_params: CreateOrderAction,
    context: AutonomousAgentContext,
    database: Any
) -> Dict[str, Any]:
    """
    Execute order creation action autonomously.
    
    Args:
        action_params: Order creation parameters
        context: Current agent context
        database: Database service instance
        
    Returns:
        Dict: Execution result with order_id and status
    """
    try:
        logger.info(f"Executing autonomous order creation for customer {context.customer_id}")
        
        # Convert action parameters to OrderProduct objects
        order_products = []
        for i, product_data in enumerate(action_params.products):
            # Handle both ExtractedProduct objects and dict data
            if isinstance(product_data, dict):
                order_product = OrderProduct(
                    product_name=product_data.get('product_name', ''),
                    quantity=int(product_data.get('quantity', 1)),
                    unit=product_data.get('unit'),
                    unit_price=None,  # Will be populated from catalog
                    line_price=None,
                    ai_confidence=float(product_data.get('confidence', 0.8)),
                    original_text=product_data.get('original_text', context.current_message.get('content', '')),
                    matched_product_id=product_data.get('matched_product_id'),
                    matching_confidence=product_data.get('matching_confidence')
                )
            else:
                # Handle ExtractedProduct objects
                order_product = OrderProduct(
                    product_name=product_data.product_name,
                    quantity=product_data.quantity,
                    unit=product_data.unit,
                    unit_price=None,
                    line_price=None,
                    ai_confidence=product_data.confidence,
                    original_text=product_data.original_text,
                    matched_product_id=getattr(product_data, 'matched_product_id', None),
                    matching_confidence=getattr(product_data, 'matching_confidence', None)
                )
            
            order_products.append(order_product)
        
        # Create order using existing order creation logic
        order_creation = OrderCreation(
            customer_id=context.customer_id,
            distributor_id=context.distributor_id,
            conversation_id=context.conversation_id,
            channel=context.current_message.get('channel', 'WHATSAPP'),
            products=order_products,
            delivery_date=action_params.delivery_date,
            additional_comment=action_params.customer_notes,
            ai_confidence=action_params.confidence_override or 0.85,
            source_message_ids=[context.current_message.get('id', '')],
            is_consolidated=False,  # This is a single-message order
            order_session_id=None
        )
        
        # Create the order
        order_id = await create_order(database, order_creation)
        
        if order_id:
            logger.info(f"✅ Autonomous agent created order {order_id} for customer {context.customer_id}")
            
            # Send confirmation message to customer
            confirmation_message = _generate_order_confirmation(order_products, order_id)
            await create_distributor_message(
                database=database,
                conversation_id=context.conversation_id,
                content=confirmation_message,
                distributor_id=context.distributor_id,
                message_type='TEXT'
            )
            
            return {
                'success': True,
                'order_id': order_id,
                'products_count': len(order_products),
                'message': 'Order created successfully by autonomous agent'
            }
        else:
            logger.error(f"❌ Failed to create autonomous order for customer {context.customer_id}")
            return {
                'success': False,
                'error': 'Order creation failed',
                'message': 'Unable to create order due to system error'
            }
            
    except Exception as e:
        logger.error(f"Failed to execute create order action: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Order creation failed due to unexpected error'
        }


async def execute_ask_clarification_action(
    action_params: AskClarificationAction,
    context: AutonomousAgentContext,
    database: Any
) -> Dict[str, Any]:
    """
    Execute clarification request action.
    
    Args:
        action_params: Clarification parameters
        context: Current agent context
        database: Database service instance
        
    Returns:
        Dict: Execution result
    """
    try:
        logger.info(f"Executing clarification request for customer {context.customer_id}")
        
        # Send clarification message to customer
        message_id = await create_distributor_message(
            database=database,
            conversation_id=context.conversation_id,
            content=action_params.question,
            distributor_id=context.distributor_id,
            message_type='TEXT'
        )
        
        if message_id:
            logger.info(f"✅ Sent clarification question to customer {context.customer_id}")
            return {
                'success': True,
                'message_id': message_id,
                'question_sent': action_params.question,
                'message': 'Clarification question sent successfully'
            }
        else:
            return {
                'success': False,
                'error': 'Failed to send clarification message',
                'message': 'Unable to send clarification question'
            }
            
    except Exception as e:
        logger.error(f"Failed to execute clarification action: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Clarification request failed'
        }


async def execute_suggest_products_action(
    action_params: SuggestProductsAction,
    context: AutonomousAgentContext,
    database: Any
) -> Dict[str, Any]:
    """
    Execute product suggestion action.
    
    Args:
        action_params: Product suggestion parameters
        context: Current agent context
        database: Database service instance
        
    Returns:
        Dict: Execution result
    """
    try:
        logger.info(f"Executing product suggestions for customer {context.customer_id}")
        
        # Generate product suggestion message
        suggestion_message = await _generate_product_suggestions(
            action_params.suggested_products,
            action_params.suggestion_reason,
            action_params.include_pricing,
            context.distributor_id,
            database
        )
        
        # Send suggestion message to customer
        message_id = await create_distributor_message(
            database=database,
            conversation_id=context.conversation_id,
            content=suggestion_message,
            distributor_id=context.distributor_id,
            message_type='TEXT'
        )
        
        if message_id:
            logger.info(f"✅ Sent product suggestions to customer {context.customer_id}")
            return {
                'success': True,
                'message_id': message_id,
                'products_suggested': len(action_params.suggested_products),
                'message': 'Product suggestions sent successfully'
            }
        else:
            return {
                'success': False,
                'error': 'Failed to send product suggestions',
                'message': 'Unable to send product suggestions'
            }
            
    except Exception as e:
        logger.error(f"Failed to execute product suggestion action: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Product suggestion failed'
        }


async def execute_provide_information_action(
    action_params: ProvideInformationAction,
    context: AutonomousAgentContext,
    database: Any
) -> Dict[str, Any]:
    """
    Execute information provision action.
    
    Args:
        action_params: Information parameters
        context: Current agent context
        database: Database service instance
        
    Returns:
        Dict: Execution result
    """
    try:
        logger.info(f"Executing information provision for customer {context.customer_id}")
        
        # Format information message
        info_message = action_params.content
        if action_params.include_next_steps:
            info_message += "\n\n¿Hay algo más en lo que pueda ayudarte?"
        
        # Send information message to customer
        message_id = await create_distributor_message(
            database=database,
            conversation_id=context.conversation_id,
            content=info_message,
            distributor_id=context.distributor_id,
            message_type='TEXT'
        )
        
        if message_id:
            logger.info(f"✅ Provided information to customer {context.customer_id}")
            return {
                'success': True,
                'message_id': message_id,
                'information_type': action_params.information_type,
                'message': 'Information provided successfully'
            }
        else:
            return {
                'success': False,
                'error': 'Failed to send information message',
                'message': 'Unable to provide information'
            }
            
    except Exception as e:
        logger.error(f"Failed to execute information provision action: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Information provision failed'
        }


async def execute_update_preferences_action(
    action_params: UpdatePreferencesAction,
    context: AutonomousAgentContext,
    memory_service: Any
) -> Dict[str, Any]:
    """
    Execute customer preference update action.
    
    Args:
        action_params: Preference update parameters
        context: Current agent context
        memory_service: Conversation memory service
        
    Returns:
        Dict: Execution result
    """
    try:
        logger.info(f"Executing preference updates for customer {context.customer_id}")
        
        updated_count = 0
        for pref_data in action_params.preferences:
            preference = CustomerPreference(
                preference_type=pref_data['type'],
                value=pref_data['value'],
                confidence=action_params.confidence,
                learned_from=context.current_message.get('id', 'autonomous_agent')
            )
            
            success = await memory_service.learn_customer_preference(
                context.customer_id,
                context.distributor_id,
                preference
            )
            
            if success:
                updated_count += 1
        
        logger.info(f"✅ Updated {updated_count} preferences for customer {context.customer_id}")
        return {
            'success': True,
            'preferences_updated': updated_count,
            'total_preferences': len(action_params.preferences),
            'message': f'Updated {updated_count} customer preferences'
        }
            
    except Exception as e:
        logger.error(f"Failed to execute preference update action: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Preference update failed'
        }


async def execute_provide_pricing_action(
    action_params: ProvidePricingAction,
    context: AutonomousAgentContext,
    database: Any
) -> Dict[str, Any]:
    """
    Execute pricing information action.
    
    Args:
        action_params: Pricing action parameters
        context: Current agent context
        database: Database service instance
        
    Returns:
        Dict: Execution result with pricing information
    """
    try:
        logger.info(f"Providing pricing information for: {action_params.message_content}")
        
        # Extract product names from message using simple keyword matching
        message_lower = action_params.message_content.lower()
        
        # Try to identify specific products mentioned
        # Query products table to find matches
        products_query = """
        SELECT name, price, unit, in_stock 
        FROM products 
        WHERE LOWER(name) LIKE ANY(ARRAY[%s])
        ORDER BY name
        """
        
        # Simple product extraction - look for common products
        common_products = ["leche", "pan", "cerveza", "pepsi", "coca", "agua", "arroz", "azucar"]
        found_products = [product for product in common_products if product in message_lower]
        
        if found_products:
            # Query specific products
            like_patterns = [f'%{product}%' for product in found_products]
            products = await database.execute_query(products_query, like_patterns)
        else:
            # No specific products found - could be asking for general pricing
            # Just return a message asking for specifics
            response_message = "¿De qué producto específico necesitas el precio?"
            
            message_id = await create_distributor_message(
                database,
                context.conversation_id,
                response_message,
                context.distributor_id
            )
            
            return {
                'success': True,
                'action': 'provide_pricing',
                'message_id': message_id,
                'response': response_message,
                'products_found': 0
            }
        
        if products:
            # Format pricing response - concise business style
            price_list = []
            for product in products:
                if product.get('in_stock', True):
                    price_list.append(f"{product['name']}: ${product['price']}")
                else:
                    price_list.append(f"{product['name']}: Sin stock")
            
            response_message = "\n".join(price_list)
        else:
            response_message = "Producto no encontrado en catálogo"
        
        # Send response message
        message_id = await create_distributor_message(
            database,
            context.conversation_id,
            response_message,
            context.distributor_id
        )
        
        return {
            'success': True,
            'action': 'provide_pricing',
            'message_id': message_id,
            'response': response_message,
            'products_found': len(products) if products else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to execute pricing action: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Pricing query failed'
        }


async def execute_check_availability_action(
    action_params: CheckAvailabilityAction,
    context: AutonomousAgentContext,
    database: Any
) -> Dict[str, Any]:
    """
    Execute availability check action.
    
    Args:
        action_params: Availability action parameters
        context: Current agent context
        database: Database service instance
        
    Returns:
        Dict: Execution result with availability information
    """
    try:
        logger.info(f"Checking availability for: {action_params.message_content}")
        
        message_lower = action_params.message_content.lower()
        
        # Extract product names using simple matching
        common_products = ["leche", "pan", "cerveza", "pepsi", "coca", "agua", "arroz", "azucar"]
        found_products = [product for product in common_products if product in message_lower]
        
        if found_products:
            # Query availability
            availability_query = """
            SELECT name, in_stock, stock_quantity, unit
            FROM products 
            WHERE LOWER(name) LIKE ANY(ARRAY[%s])
            ORDER BY name
            """
            
            like_patterns = [f'%{product}%' for product in found_products]
            products = await database.execute_query(availability_query, like_patterns)
        else:
            # Ask for specific product
            response_message = "¿De qué producto necesitas verificar disponibilidad?"
            
            message_id = await create_distributor_message(
                database,
                context.conversation_id,
                response_message,
                context.distributor_id
            )
            
            return {
                'success': True,
                'action': 'check_availability',
                'message_id': message_id,
                'response': response_message,
                'products_found': 0
            }
        
        if products:
            # Format availability response - concise business style
            availability_list = []
            for product in products:
                if product.get('in_stock', True):
                    quantity = product.get('stock_quantity', 'Disponible')
                    if isinstance(quantity, (int, float)) and quantity > 0:
                        availability_list.append(f"{product['name']}: {int(quantity)} {product.get('unit', 'unidades')}")
                    else:
                        availability_list.append(f"{product['name']}: Disponible")
                else:
                    availability_list.append(f"{product['name']}: Sin stock")
            
            response_message = "\n".join(availability_list)
        else:
            response_message = "Producto no encontrado en catálogo"
        
        # Send response message
        message_id = await create_distributor_message(
            database,
            context.conversation_id,
            response_message,
            context.distributor_id
        )
        
        return {
            'success': True,
            'action': 'check_availability',
            'message_id': message_id,
            'response': response_message,
            'products_found': len(products) if products else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to execute availability check: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Availability check failed'
        }


async def execute_do_nothing_action(
    context: AutonomousAgentContext
) -> Dict[str, Any]:
    """
    Do nothing - let conversation flow naturally.
    
    Args:
        context: Current agent context
        
    Returns:
        Dict: Execution result indicating no action taken
    """
    logger.info(f"🔇 DO_NOTHING: No action needed for message {context.current_message.get('id')}")
    
    return {
        'success': True,
        'action': 'do_nothing',
        'message': 'No action taken - non-order message',
        'send_response': False  # Important: Don't send any response
    }


async def execute_escalate_to_human_action(
    context: AutonomousAgentContext,
    database: Any,
    escalation_reason: str = "Autonomous agent requires human assistance"
) -> Dict[str, Any]:
    """
    Execute escalation to human action.
    
    Args:
        context: Current agent context
        database: Database service instance
        escalation_reason: Reason for escalation
        
    Returns:
        Dict: Execution result
    """
    try:
        logger.info(f"Executing escalation to human for customer {context.customer_id}")
        
        # Create escalation message for internal tracking
        escalation_message = f"🚨 ESCALACIÓN AUTOMÁTICA\n\n" \
                           f"Razón: {escalation_reason}\n" \
                           f"Cliente: {context.customer_id}\n" \
                           f"Conversación: {context.conversation_id}\n" \
                           f"Mensaje: {context.current_message.get('content', '')[:100]}...\n\n" \
                           f"Un agente humano revisará este caso."
        
        # Send escalation notification (this would typically go to a human agent interface)
        # For now, we'll just log it and potentially send a holding message to customer
        
        customer_message = "Estoy revisando tu solicitud con cuidado. " \
                          "Un miembro de nuestro equipo te contactará pronto para ayudarte mejor."
        
        message_id = await create_distributor_message(
            database=database,
            conversation_id=context.conversation_id,
            content=customer_message,
            distributor_id=context.distributor_id,
            message_type='TEXT'
        )
        
        logger.warning(f"🚨 ESCALATED to human: {escalation_reason} for customer {context.customer_id}")
        
        return {
            'success': True,
            'message_id': message_id,
            'escalation_reason': escalation_reason,
            'message': 'Successfully escalated to human agent'
        }
            
    except Exception as e:
        logger.error(f"Failed to execute escalation action: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Escalation failed'
        }


def _generate_order_confirmation(products: List[OrderProduct], order_id: str) -> str:
    """Generate order confirmation message."""
    
    confirmation = f"✅ ¡Perfecto! He creado tu pedido #{order_id[-8:]} con:\n\n"
    
    for i, product in enumerate(products, 1):
        unit_text = f" {product.unit}" if product.unit else ""
        confirmation += f"{i}. {product.quantity}{unit_text} de {product.product_name}\n"
    
    confirmation += f"\nTu pedido está siendo procesado. Te contactaremos pronto con los detalles de entrega."
    
    return confirmation


async def _generate_product_suggestions(
    suggested_products: List[Dict[str, Any]],
    reason: str,
    include_pricing: bool,
    distributor_id: str,
    database: Any
) -> str:
    """Generate product suggestion message."""
    
    message = f"💡 {reason}\n\n"
    
    # Get product catalog for pricing if needed
    catalog = {}
    if include_pricing:
        try:
            catalog_products = await fetch_product_catalog(database, distributor_id, active_only=True)
            catalog = {p.id: p for p in catalog_products}
        except:
            pass
    
    for i, product in enumerate(suggested_products, 1):
        product_name = product.get('name', product.get('product_name', 'Producto'))
        
        message += f"{i}. {product_name}"
        
        if include_pricing and product.get('id') in catalog:
            price = catalog[product['id']].unit_price
            if price:
                message += f" - ${float(price):.2f}"
        
        if product.get('description'):
            message += f"\n   {product['description']}"
        
        message += "\n\n"
    
    message += "¿Te interesa alguno de estos productos?"
    
    return message


# Action execution mapping
ACTION_EXECUTORS = {
    AutonomousActionType.DO_NOTHING: lambda params, context, database: execute_do_nothing_action(context),
    AutonomousActionType.CREATE_ORDER: execute_create_order_action,
    AutonomousActionType.ASK_CLARIFICATION: execute_ask_clarification_action,
    AutonomousActionType.SUGGEST_PRODUCTS: execute_suggest_products_action,
    AutonomousActionType.PROVIDE_PRICING: execute_provide_pricing_action,
    AutonomousActionType.CHECK_AVAILABILITY: execute_check_availability_action,
    AutonomousActionType.PROVIDE_INFORMATION: execute_provide_information_action,
    AutonomousActionType.UPDATE_CUSTOMER_PREFERENCES: execute_update_preferences_action,
    AutonomousActionType.ESCALATE_TO_HUMAN: lambda params, context, database: execute_escalate_to_human_action(context, database)
}


async def execute_autonomous_action(
    action: AutonomousAction,
    context: AutonomousAgentContext,
    database: Any,
    memory_service: Any = None
) -> Dict[str, Any]:
    """
    Execute any autonomous action with proper parameter handling.
    
    Args:
        action: Action to execute
        context: Current agent context
        database: Database service instance
        memory_service: Memory service instance (for preference updates)
        
    Returns:
        Dict: Execution result
    """
    try:
        logger.info(f"Executing autonomous action: {action.action_type}")
        
        # Get the appropriate executor
        if action.action_type not in ACTION_EXECUTORS:
            logger.error(f"Unknown action type: {action.action_type}")
            return {
                'success': False,
                'error': f'Unknown action type: {action.action_type}',
                'message': 'Action execution failed'
            }
        
        executor = ACTION_EXECUTORS[action.action_type]
        
        # Execute action with appropriate parameters
        if action.action_type == AutonomousActionType.DO_NOTHING:
            # No parameters needed for DO_NOTHING
            return await executor(None, context, database)
        
        elif action.action_type == AutonomousActionType.CREATE_ORDER:
            action_params = CreateOrderAction(**action.parameters)
            return await executor(action_params, context, database)
        
        elif action.action_type == AutonomousActionType.ASK_CLARIFICATION:
            action_params = AskClarificationAction(**action.parameters)
            return await executor(action_params, context, database)
        
        elif action.action_type == AutonomousActionType.SUGGEST_PRODUCTS:
            action_params = SuggestProductsAction(**action.parameters)
            return await executor(action_params, context, database)
        
        elif action.action_type == AutonomousActionType.PROVIDE_PRICING:
            action_params = ProvidePricingAction(**action.parameters)
            return await executor(action_params, context, database)
        
        elif action.action_type == AutonomousActionType.CHECK_AVAILABILITY:
            action_params = CheckAvailabilityAction(**action.parameters)
            return await executor(action_params, context, database)
        
        elif action.action_type == AutonomousActionType.PROVIDE_INFORMATION:
            action_params = ProvideInformationAction(**action.parameters)
            return await executor(action_params, context, database)
        
        elif action.action_type == AutonomousActionType.UPDATE_CUSTOMER_PREFERENCES:
            if not memory_service:
                raise ValueError("Memory service required for preference updates")
            action_params = UpdatePreferencesAction(**action.parameters)
            return await executor(action_params, context, memory_service)
        
        elif action.action_type == AutonomousActionType.ESCALATE_TO_HUMAN:
            escalation_reason = action.parameters.get('reason', 'Autonomous agent requires assistance')
            return await executor(context, database, escalation_reason)
        
        else:
            return {
                'success': False,
                'error': f'Action type {action.action_type} not fully implemented',
                'message': 'Action execution not available'
            }
            
    except Exception as e:
        logger.error(f"Failed to execute autonomous action {action.action_type}: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Action execution failed due to unexpected error'
        }