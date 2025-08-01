"""
Supabase database tools for the Order Agent system.

Provides async functions for database operations including message processing,
order creation, and product catalog management. Uses dependency injection pattern
from examples/example_pydantic_ai.py.

CRITICAL: Always filter by distributor_id for multi-tenancy
CRITICAL: Use database transactions for atomic operations
"""

from __future__ import annotations as _annotations

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from services.database import DatabaseService
from schemas.message import MessageAnalysis, MessageUpdate
from schemas.order import OrderCreation, OrderDatabaseInsert, OrderProductDatabaseInsert, OrderProduct
from schemas.product import CatalogProduct

logger = logging.getLogger(__name__)


async def create_distributor_message(
    database: DatabaseService,
    conversation_id: str,
    content: str,
    distributor_id: str,
    message_type: str = 'TEXT'
) -> Optional[str]:
    """
    Create a message from the distributor (AI agent response).
    
    Args:
        database: Database service instance
        conversation_id: ID of the conversation
        content: Message content to send
        distributor_id: Distributor ID
        message_type: Type of message (default: TEXT)
        
    Returns:
        Message ID if successful, None if failed
    """
    try:
        message_data = {
            'conversation_id': conversation_id,
            'content': content,
            'is_from_customer': False,  # This is from the distributor/AI
            'message_type': message_type,
            'status': 'SENT',
            'ai_processed': False,  # This is an AI-generated message, not processed by AI
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = await database.insert_single(
            table='messages',
            data=message_data
        )
        
        if result:
            message_id = result.get('id')
            logger.info(f"✅ Created distributor message {message_id} in conversation {conversation_id}")
            return message_id
        
        logger.error("Failed to create distributor message - no result returned")
        return None
        
    except Exception as e:
        logger.error(f"❌ Failed to create distributor message: {e}")
        return None


async def fetch_unprocessed_messages(
    db: DatabaseService, 
    distributor_id: str, 
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch unprocessed messages from the database.
    
    Note: messages table doesn't have distributor_id column. Security enforced by RLS.
    In practice, you'd use a JOIN or stored procedure to filter by distributor.
    
    Args:
        db: Database service instance
        distributor_id: Distributor ID (for logging, actual filtering via RLS)
        limit: Maximum number of messages to fetch
        
    Returns:
        List[Dict[str, Any]]: List of unprocessed message records
    """
    try:
        logger.info(f"Fetching up to {limit} unprocessed messages for distributor {distributor_id}")
        
        # Get unprocessed customer messages (RLS policies enforce tenant isolation)
        messages = await db.execute_query(
            table='messages',
            operation='select',
            filters={
                'ai_processed': False,
                'is_from_customer': True  # Only process customer messages
            },
            distributor_id=None  # Explicitly set to None - messages table doesn't have this column
        )
        
        # Limit results and sort by created_at
        if messages:
            # Sort by created_at to process messages in order
            messages.sort(key=lambda x: x.get('created_at', ''))
            messages = messages[:limit]
        
        logger.info(f"Found {len(messages) if messages else 0} unprocessed messages")
        return messages or []
        
    except Exception as e:
        logger.error(f"Failed to fetch unprocessed messages: {e}")
        raise


async def update_message_ai_data(
    db: DatabaseService,
    message_id: str,
    analysis: MessageAnalysis,
    distributor_id: str
) -> bool:
    """
    Update message with AI analysis results.
    
    Uses direct message ID update (no distributor_id filtering needed since 
    message_id is unique and we trust the caller has permission).
    
    Args:
        db: Database service instance
        message_id: Message ID to update
        analysis: Complete message analysis
        distributor_id: Distributor ID (for logging, not filtering)
        
    Returns:
        bool: True if update successful
    """
    try:
        logger.debug(f"Updating message {message_id} with AI analysis")
        
        # Create update data directly with the fields we know exist
        # Use model_dump() for Pydantic v2 compatibility and add better logging
        products_json = None
        if analysis.extracted_products:
            try:
                # Use model_dump() for Pydantic v2 compatibility
                products_json = [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in analysis.extracted_products]
                logger.info(f"Serializing {len(products_json)} products: {[p.get('product_name') for p in products_json]}")
            except Exception as e:
                logger.error(f"Failed to serialize products: {e}")
                products_json = None
        
        update_data = {
            'ai_processed': True,
            'ai_confidence': analysis.intent.confidence,
            'ai_extracted_intent': analysis.intent.intent,
            'ai_extracted_products': products_json,
            'ai_processing_time_ms': analysis.processing_time_ms,
            'updated_at': datetime.now().isoformat()
        }
        
        logger.debug(f"Update data for message {message_id}: {update_data}")
        
        # Update message by ID only (no distributor_id needed - message IDs are unique)
        result = await db.update_single(
            table='messages',
            data=update_data,
            filters={'id': message_id},
            distributor_id=None  # Explicitly set to None to prevent filtering
        )
        
        success = result is not None
        if success:
            logger.info(f"✅ Updated message {message_id} with AI analysis (confidence: {analysis.intent.confidence:.2f})")
            if products_json:
                logger.info(f"   Products saved: {[p.get('product_name') for p in products_json]}")
        else:
            logger.error(f"❌ Failed to update message {message_id} - no rows affected. Check if message exists in database.")
            
        return success
        
    except Exception as e:
        logger.error(f"Failed to update message AI data: {e}")
        return False


async def create_order(
    db: DatabaseService,
    order_data: OrderCreation
) -> Optional[str]:
    """
    Create order with transaction for order + order_products.
    
    CRITICAL: Use transaction for order + order_products creation
    
    Args:
        db: Database service instance
        order_data: Complete order creation data
        
    Returns:
        Optional[str]: Order ID if successful, None if failed
    """
    try:
        logger.info(f"Creating order for customer {order_data.customer_id} with {len(order_data.products)} products")
        
        # CRITICAL: Use database transactions for atomic operations
        async with db.transaction() as tx:
            # PATTERN: Insert order record first
            # Calculate total_amount - use 0 for orders without pricing (testing phase)
            calculated_total = order_data.total_amount or Decimal('0')
            order_insert = OrderDatabaseInsert.from_order_creation(order_data, calculated_total)
            
            # Debug logging
            logger.debug(f"Order insert data: {order_insert.dict()}")
            logger.debug(f"Total amount: {order_insert.total_amount} (type: {type(order_insert.total_amount)})")
            
            # Convert Decimal to float for JSON serialization
            order_data_dict = order_insert.dict()
            if order_data_dict.get('total_amount') is not None:
                order_data_dict['total_amount'] = float(order_data_dict['total_amount'])
            
            order_result = await tx.execute_query(
                table='orders',
                operation='insert',
                data=order_data_dict,
                distributor_id=order_data.distributor_id
            )
            
            if not order_result or len(order_result) == 0:
                logger.error("Failed to insert order record")
                return None
            
            order_id = order_result[0]['id']
            logger.debug(f"Created order record with ID: {order_id}")
            
            # PATTERN: Insert order products as separate records
            # First, populate catalog prices for matched products
            await _populate_catalog_prices(tx, order_data.products, order_data.distributor_id)
            
            products_to_insert = []
            for line_order, product in enumerate(order_data.products, 1):
                product_insert = OrderProductDatabaseInsert.from_order_product(
                    product, order_id, line_order
                )
                product_dict = product_insert.dict()
                
                # Convert Decimal fields to float for JSON serialization
                if product_dict.get('unit_price') is not None:
                    product_dict['unit_price'] = float(product_dict['unit_price'])
                if product_dict.get('line_price') is not None:
                    product_dict['line_price'] = float(product_dict['line_price'])
                
                products_to_insert.append(product_dict)
                
                # Debug: Log the product data being inserted
                logger.debug(f"Product to insert: {product_dict}")
            
            if products_to_insert:
                try:
                    products_result = await tx.execute_query(
                        table='order_products',
                        operation='insert',
                        data=products_to_insert,
                        distributor_id=None  # order_products table doesn't have distributor_id column
                    )
                    
                    if not products_result:
                        logger.error("Failed to insert order products")
                        return None
                    
                    logger.debug(f"Created {len(products_to_insert)} order product records")
                except Exception as e:
                    logger.error(f"Order products insertion failed: {e}")
                    # Log detailed error information
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        logger.error(f"Response text: {e.response.text}")
                    elif hasattr(e, 'response') and hasattr(e.response, 'json'):
                        try:
                            error_json = e.response.json()
                            logger.error(f"Response JSON: {error_json}")
                        except:
                            logger.error(f"Could not parse response JSON")
                    logger.error(f"Product data being inserted: {products_to_insert}")
                    return None
            
            logger.info(f"Successfully created order {order_id} with {len(products_to_insert)} products")
            return order_id
            
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        return None


async def fetch_product_catalog(
    db: DatabaseService,
    distributor_id: str,
    active_only: bool = True
) -> List[CatalogProduct]:
    """
    Fetch product catalog for matching.
    
    Args:
        db: Database service instance
        distributor_id: Distributor ID for multi-tenant filtering
        active_only: Only fetch active products
        
    Returns:
        List[CatalogProduct]: List of catalog products
    """
    try:
        logger.info(f"Fetching product catalog for distributor {distributor_id}")
        
        filters = {}
        if active_only:
            filters['active'] = True
        
        # Get products with aliases and keywords for matching
        products = await db.execute_query(
            table='products',
            operation='select',
            filters=filters,
            distributor_id=distributor_id
        )
        
        if not products:
            logger.warning(f"No products found for distributor {distributor_id}")
            return []
        
        # Convert to CatalogProduct objects
        catalog_products = []
        for product in products:
            try:
                catalog_product = CatalogProduct(
                    id=product['id'],
                    name=product['name'],
                    sku=product.get('sku'),
                    description=product.get('description'),
                    category=product.get('category'),
                    unit=product.get('unit'),
                    unit_price=product.get('unit_price'),
                    brand=product.get('brand'),
                    aliases=product.get('aliases', []) or [],
                    keywords=product.get('keywords', []) or [],
                    ai_training_examples=product.get('ai_training_examples', []) or [],
                    common_misspellings=product.get('common_misspellings', []) or [],
                    in_stock=product.get('in_stock', True),
                    active=product.get('active', True)
                )
                catalog_products.append(catalog_product)
            except Exception as e:
                logger.warning(f"Failed to parse product {product.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Loaded {len(catalog_products)} products from catalog")
        return catalog_products
        
    except Exception as e:
        logger.error(f"Failed to fetch product catalog: {e}")
        return []


async def get_customer_info(
    db: DatabaseService,
    customer_id: str,
    distributor_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get customer information for order processing.
    
    Args:
        db: Database service instance
        customer_id: Customer ID to look up
        distributor_id: Distributor ID for multi-tenant filtering
        
    Returns:
        Optional[Dict[str, Any]]: Customer information if found
    """
    try:
        customers = await db.execute_query(
            table='customers',
            operation='select',
            filters={'id': customer_id},
            distributor_id=distributor_id
        )
        
        if customers and len(customers) > 0:
            return customers[0]
        
        logger.warning(f"Customer {customer_id} not found")
        return None
        
    except Exception as e:
        logger.error(f"Failed to get customer info: {e}")
        return None


async def get_conversation_info(
    db: DatabaseService,
    conversation_id: str,
    distributor_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get conversation information for context.
    
    Args:
        db: Database service instance
        conversation_id: Conversation ID to look up
        distributor_id: Distributor ID for multi-tenant filtering
        
    Returns:
        Optional[Dict[str, Any]]: Conversation information if found
    """
    try:
        conversations = await db.execute_query(
            table='conversations',
            operation='select',
            filters={'id': conversation_id},
            distributor_id=distributor_id
        )
        
        if conversations and len(conversations) > 0:
            return conversations[0]
        
        logger.warning(f"Conversation {conversation_id} not found")
        return None
        
    except Exception as e:
        logger.error(f"Failed to get conversation info: {e}")
        return None


async def update_conversation_context(
    db: DatabaseService,
    conversation_id: str,
    context_summary: str,
    distributor_id: str
) -> bool:
    """
    Update conversation with AI context summary.
    
    Args:
        db: Database service instance
        conversation_id: Conversation ID to update
        context_summary: AI-generated context summary
        distributor_id: Distributor ID for multi-tenant filtering
        
    Returns:
        bool: True if update successful
    """
    try:
        result = await db.execute_query(
            table='conversations',
            operation='update',
            data={
                'ai_context_summary': context_summary,
                'ai_last_processed_at': datetime.now().isoformat()
            },
            filters={'id': conversation_id},
            distributor_id=distributor_id
        )
        
        return result is not None and len(result) > 0
        
    except Exception as e:
        logger.error(f"Failed to update conversation context: {e}")
        return False


async def get_recent_messages_for_context(
    db: DatabaseService,
    conversation_id: str,
    distributor_id: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get recent messages from a conversation for context.
    
    Uses simple conversation_id filter since messages table doesn't have distributor_id.
    Security is enforced by RLS policies at database level.
    
    Args:
        db: Database service instance
        conversation_id: Conversation ID to get messages from
        distributor_id: Distributor ID (for logging only, security via RLS)
        limit: Maximum number of messages to fetch
        
    Returns:
        List[Dict[str, Any]]: Recent messages for context
    """
    try:
        logger.debug(f"Getting recent messages for conversation {conversation_id} (distributor: {distributor_id})")
        
        # Get messages from conversation (security enforced by RLS)
        messages = await db.execute_query(
            table='messages',
            operation='select',
            filters={'conversation_id': conversation_id},
            distributor_id=None  # Explicitly set to None - messages table doesn't have this column
        )
        
        if messages:
            # Sort by created_at descending and take the most recent
            messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return messages[:limit]
        
        return []
        
    except Exception as e:
        logger.error(f"Failed to get recent messages: {e}")
        return []


async def get_recent_orders(
    db: DatabaseService,
    customer_id: str,
    distributor_id: str,
    hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Get recent orders from a customer for context.
    
    Orders table already has distributor_id, so this should work correctly.
    
    Args:
        db: Database service instance
        customer_id: Customer ID to get orders from
        distributor_id: Distributor ID for multi-tenant filtering
        hours: Number of hours back to search (default 24)
        
    Returns:
        List[Dict[str, Any]]: Recent orders for context
    """
    try:
        # Orders table has distributor_id column, so this should work
        orders = await db.execute_query(
            table='orders',
            operation='select',
            filters={'customer_id': customer_id},
            distributor_id=distributor_id
        )
        
        if orders:
            # Sort by created_at descending and take recent ones
            orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # For simplicity, return last 5 orders (time filtering can be added later)
            return orders[:5]
        
        return []
        
    except Exception as e:
        logger.error(f"Failed to get recent orders: {e}")
        return []


async def _populate_catalog_prices(
    db: DatabaseService,
    products: List[OrderProduct],
    distributor_id: str
) -> None:
    """
    Populate unit_price and line_price from product catalog for matched products.
    
    Modifies the OrderProduct objects in-place to set correct prices from catalog.
    
    Args:
        db: Database service instance (or transaction)
        products: List of OrderProduct objects to populate prices for
        distributor_id: Distributor ID for multi-tenant filtering
    """
    try:
        # Find products that have matched_product_id but missing prices
        products_needing_prices = []
        product_ids_to_lookup = set()
        
        for product in products:
            if (product.matched_product_id and 
                (product.unit_price is None or product.unit_price == 0)):
                products_needing_prices.append(product)
                product_ids_to_lookup.add(product.matched_product_id)
        
        if not product_ids_to_lookup:
            logger.debug("No products need catalog price lookup")
            return
        
        logger.info(f"Looking up catalog prices for {len(product_ids_to_lookup)} matched products")
        
        # Fetch catalog prices for matched products
        # Use IN query for multiple IDs
        catalog_data = []
        for product_id in product_ids_to_lookup:
            result = await db.execute_query(
                table='products',
                operation='select',
                filters={'id': product_id},
                distributor_id=distributor_id
            )
            if result:
                catalog_data.extend(result)
        
        if not catalog_data:
            logger.warning("No catalog data found for matched products")
            return
        
        # Create lookup map: product_id -> catalog_price
        price_lookup = {}
        for catalog_item in catalog_data:
            product_id = catalog_item['id']
            unit_price = catalog_item.get('unit_price')
            if unit_price is not None:
                price_lookup[product_id] = Decimal(str(unit_price))
                logger.debug(f"Found catalog price for {product_id}: ${unit_price}")
        
        # Update products with catalog prices
        updated_count = 0
        for product in products_needing_prices:
            if product.matched_product_id in price_lookup:
                catalog_price = price_lookup[product.matched_product_id]
                
                # Set unit_price from catalog
                product.unit_price = catalog_price
                
                # Calculate line_price = quantity × unit_price
                product.line_price = catalog_price * product.quantity
                
                logger.info(f"✅ Updated prices for '{product.product_name}': "
                           f"unit_price=${catalog_price}, "
                           f"line_price=${product.line_price} "
                           f"(qty={product.quantity})")
                updated_count += 1
        
        logger.info(f"Successfully populated catalog prices for {updated_count} products")
        
    except Exception as e:
        logger.error(f"Failed to populate catalog prices: {e}")
        # Don't raise - allow order creation to continue with 0.00 prices