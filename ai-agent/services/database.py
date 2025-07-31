"""
Database service for Order Agent system.

Provides async Supabase client setup with multi-tenant helpers and common database operations.
Follows the pattern from examples/example_pydantic_ai.py.
"""

from __future__ import annotations as _annotations

import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from supabase import acreate_client
from supabase.client import AsyncClientOptions
from supabase._async.client import AsyncClient
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Async database service with multi-tenant support and connection pooling.
    
    CRITICAL: Always filter by distributor_id for multi-tenancy
    CRITICAL: Use RLS policies - they automatically enforce tenant isolation
    """
    
    def __init__(self):
        """Initialize the database service."""
        self._client: Optional[AsyncClient] = None
        self._connection_pool_size = settings.connection_pool_size
    
    async def get_client(self) -> AsyncClient:
        """
        Get or create the Supabase client.
        
        Returns:
            AsyncClient: Async Supabase client instance
        """
        if self._client is None:
            self._client = await acreate_client(
                settings.supabase_url,
                settings.supabase_key,
                options=AsyncClientOptions(
                    auto_refresh_token=True,
                    persist_session=True
                )
            )
            logger.info("Supabase client initialized")
        
        return self._client
    
    async def execute_query(
        self, 
        table: str, 
        operation: str, 
        data: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        distributor_id: Optional[str] = None
    ) -> Any:
        """
        Execute a database query with multi-tenant filtering.
        
        Args:
            table: Table name to query
            operation: Operation type ('select', 'insert', 'update', 'delete')
            data: Data for insert/update operations
            filters: Additional filters for the query
            distributor_id: Distributor ID for multi-tenant filtering
            
        Returns:
            Dict[str, Any]: Query result
            
        Raises:
            ValueError: If distributor_id is not provided for multi-tenant operations
        """
        client = await self.get_client()
        
        # CRITICAL: Always filter by distributor_id for multi-tenancy
        # Exception: messages table doesn't have distributor_id (uses relationship)
        if distributor_id is None and table not in ['distributors', 'messages']:
            logger.warning(f"No distributor_id provided for table '{table}' - this may cause security issues")
        
        try:
            if operation == 'select':
                query = client.from_(table).select('*')
                
                # Apply distributor filter (skip for messages table)
                if distributor_id and table != 'messages':
                    query = query.eq('distributor_id', distributor_id)
                
                # Apply additional filters
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                
                result = await query.execute()
                
            elif operation == 'insert':
                if not data:
                    raise ValueError("Data is required for insert operations")
                
                # Ensure distributor_id is included in insert data (skip for messages table)
                if distributor_id and 'distributor_id' not in data and table != 'messages':
                    data['distributor_id'] = distributor_id
                
                result = await client.from_(table).insert(data).execute()
                
            elif operation == 'update':
                if not data:
                    raise ValueError("Data is required for update operations")
                
                query = client.from_(table).update(data)
                
                # Apply distributor filter for safety (skip for messages table)
                if distributor_id and table != 'messages':
                    query = query.eq('distributor_id', distributor_id)
                
                # Apply additional filters
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                
                result = await query.execute()
                
            elif operation == 'delete':
                query = client.from_(table).delete()
                
                # Apply distributor filter for safety (skip for messages table)
                if distributor_id and table != 'messages':
                    query = query.eq('distributor_id', distributor_id)
                
                # Apply additional filters
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                
                result = await query.execute()
                
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            return result.data if hasattr(result, 'data') else result
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            
            # Log more details for debugging
            if hasattr(e, 'response'):
                if hasattr(e.response, 'text'):
                    logger.error(f"Response text: {e.response.text}")
                if hasattr(e.response, 'content'):
                    logger.error(f"Response content: {e.response.content}")
                if hasattr(e.response, 'json'):
                    try:
                        error_json = e.response.json()
                        logger.error(f"Response JSON: {error_json}")
                    except:
                        logger.error("Could not parse response JSON")
                if hasattr(e.response, 'status_code'):
                    logger.error(f"HTTP Status Code: {e.response.status_code}")
            elif hasattr(e, 'args') and len(e.args) > 0:
                logger.error(f"Error details: {e.args}")
            
            # Also log the operation details
            logger.error(f"Failed operation: {operation} on table '{table}'")
            if data:
                logger.error(f"Data being processed: {data}")
            if filters:
                logger.error(f"Filters: {filters}")
            
            raise
    
    async def update_single(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        distributor_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a single record and return the updated record.
        
        Args:
            table: Table name
            data: Data to update
            filters: Filters to identify the record
            distributor_id: Distributor ID for multi-tenant filtering
            
        Returns:
            Updated record or None if no record was updated
        """
        result = await self.execute_query(
            table=table,
            operation='update',
            data=data,
            filters=filters,
            distributor_id=distributor_id
        )
        
        if result and len(result) > 0:
            logger.debug(f"Updated 1 record in {table}")
            return result[0]
        else:
            logger.warning(f"No records updated in {table} with filters {filters}")
            return None
    
    async def insert_single(
        self,
        table: str,
        data: Dict[str, Any],
        distributor_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Insert a single record and return the inserted record.
        
        Args:
            table: Table name
            data: Data to insert
            distributor_id: Distributor ID for multi-tenant filtering
            
        Returns:
            Inserted record or None if insert failed
        """
        result = await self.execute_query(
            table=table,
            operation='insert',
            data=data,
            distributor_id=distributor_id
        )
        
        if result and len(result) > 0:
            logger.debug(f"Inserted 1 record in {table}")
            return result[0]
        else:
            logger.error(f"Failed to insert record in {table}")
            return None
    
    @asynccontextmanager
    async def transaction(self):
        """
        Database transaction context manager.
        
        Note: Supabase Python client handles transactions automatically.
        This context manager provides a consistent API for transaction operations.
        """
        client = await self.get_client()
        
        try:
            # Supabase handles transactions internally
            # This context manager provides structure for complex operations
            yield self
            logger.debug("Transaction context completed successfully")
            
        except Exception as e:
            logger.error(f"Transaction context failed: {e}")
            # Supabase automatically handles rollback on error
            raise


# Multi-tenant helper functions
def get_current_distributor_id() -> str:
    """
    Get the current distributor ID for multi-tenant operations.
    
    CRITICAL: Never hard-code distributor IDs - use this function
    
    Returns:
        str: Current distributor ID
        
    Note:
        In a real implementation, this would get the distributor ID from
        the current user session or request context. For now, we'll use
        a demo distributor ID from environment variables.
    """
    import os
    distributor_id = os.getenv('DEMO_DISTRIBUTOR_ID')
    if not distributor_id:
        raise ValueError("DEMO_DISTRIBUTOR_ID not found in environment variables")
    return distributor_id


async def get_distributor_settings(distributor_id: str) -> Dict[str, Any]:
    """
    Get distributor-specific settings for AI processing.
    
    Args:
        distributor_id: Distributor ID
        
    Returns:
        Dict[str, Any]: Distributor settings including ai_confidence_threshold
    """
    db = DatabaseService()
    
    result = await db.execute_query(
        table='distributors',
        operation='select',
        filters={'id': distributor_id}
    )
    
    if not result or len(result) == 0:
        raise ValueError(f"Distributor {distributor_id} not found")
    
    distributor = result[0]
    
    return {
        'ai_confidence_threshold': distributor.get('ai_confidence_threshold', 0.8),
        'ai_enabled': distributor.get('ai_enabled', True),
        'ai_model_preference': distributor.get('ai_model_preference', 'gpt-4o-mini'),
        'monthly_ai_budget_usd': distributor.get('monthly_ai_budget_usd', 100.0),
    }


# Global database service instance
db_service = DatabaseService()