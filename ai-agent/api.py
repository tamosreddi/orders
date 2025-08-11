"""
FastAPI HTTP API for Order Agent integration with webhook system.

Provides HTTP endpoints for triggering AI message processing from the
Next.js webhook system. Maintains the existing async architecture while
enabling real-time processing.
"""

from __future__ import annotations as _annotations

import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import settings
from services.database import DatabaseService, get_current_distributor_id
from agents.agent_factory import create_agent_factory, AgentFactory

logger = logging.getLogger(__name__)

# Global variables for initialized components
database_service: Optional[DatabaseService] = None
agent_factory: Optional[AgentFactory] = None


class MessageProcessingRequest(BaseModel):
    """Request model for message processing endpoint."""
    
    message_id: str = Field(..., description="Database ID of the message to process")
    customer_id: str = Field(..., description="Customer ID for the message")
    conversation_id: str = Field(..., description="Conversation ID for the message")
    content: str = Field(..., description="Message content to process")
    distributor_id: Optional[str] = Field(None, description="Distributor ID (auto-detected if not provided)")
    channel: str = Field(default="WHATSAPP", description="Message channel")


class MessageProcessingResponse(BaseModel):
    """Response model for message processing."""
    
    success: bool = Field(..., description="Whether processing was successful")
    message_id: str = Field(..., description="Processed message ID")
    intent: Optional[str] = Field(None, description="Classified intent")
    confidence: Optional[float] = Field(None, description="AI confidence score")
    products_extracted: int = Field(0, description="Number of products extracted")
    order_created: bool = Field(False, description="Whether an order was created")
    order_id: Optional[str] = Field(None, description="Created order ID if applicable")
    continuation_order_id: Optional[str] = Field(None, description="Continued order ID if applicable")
    processing_time_ms: int = Field(0, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="API status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")
    components: Dict[str, str] = Field(..., description="Component status")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager for initialization and cleanup."""
    global database_service, agent_factory
    
    logger.info("🚀 Starting Order Agent API with Autonomous Capabilities...")
    
    try:
        # Initialize database service
        database_service = DatabaseService()
        logger.info("✅ Database service initialized")
        
        # Get distributor ID
        distributor_id = get_current_distributor_id()
        logger.info(f"🏢 Using distributor ID: {distributor_id}")
        
        # Create agent factory for intelligent agent selection
        agent_factory = create_agent_factory(
            database_service,
            distributor_id
        )
        
        logger.info("🤖 Agent Factory initialized - will select best agent per request")
        
        # Log agent factory health status
        health_status = await agent_factory.get_agent_health_status()
        logger.info(f"🔍 Agent Factory Status: {health_status['factory_status']}")
        
        # Handle both old and new configuration structures
        if 'configuration' in health_status:
            logger.info(f"🔍 Simplified Agent Enabled: {health_status['configuration']['simplified_agent_enabled']}")
        elif 'feature_flags' in health_status:
            logger.info(f"🔍 Autonomous Agent Enabled: {health_status['feature_flags']['autonomous_enabled']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Order Agent API: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down Order Agent API...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Order Agent API",
    description="AI-powered customer message processing for B2B food distributors",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for webhook integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring and debugging."""
    
    components = {
        "database": "ok" if database_service else "not_initialized",
        "agent_factory": "ok" if agent_factory else "not_initialized",
        "settings": "ok" if settings else "error"
    }
    
    # Add agent factory health details if available
    if agent_factory:
        try:
            factory_health = await agent_factory.get_agent_health_status()
            components["autonomous_agent"] = "enabled" if factory_health['feature_flags']['autonomous_enabled'] else "disabled"
        except:
            components["autonomous_agent"] = "error"
    
    all_healthy = all(status == "ok" for status in components.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        message="Order Agent API is running" if all_healthy else "Some components not initialized",
        version="1.0.0",
        components=components
    )


@app.post("/process-message", response_model=MessageProcessingResponse)
async def process_message(
    request: MessageProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a customer message through the AI agent workflow.
    
    This endpoint is called by the webhook system after a message is stored
    in the database. It triggers the 6-step AI processing workflow.
    """
    
    logger.info(f"📨 Processing message request: {request.message_id}")
    
    if not agent_factory:
        logger.error("❌ Agent factory not initialized")
        raise HTTPException(
            status_code=503, 
            detail="Agent factory not initialized - check service health"
        )
    
    try:
        # Use provided distributor_id or detect from environment
        distributor_id = request.distributor_id or get_current_distributor_id()
        
        # Create message object for processing (simulates database message)
        message_data = {
            'id': request.message_id,
            'content': request.content,
            'customer_id': request.customer_id,
            'conversation_id': request.conversation_id,
            'channel': request.channel
        }
        
        logger.info(f"🤖 Starting AI processing for message: {request.message_id}")
        
        # Process message using the best available agent via factory
        result = await agent_factory.process_message_with_best_agent(message_data)
        
        if not result:
            logger.error(f"❌ Failed to process message: {request.message_id}")
            return MessageProcessingResponse(
                success=False,
                message_id=request.message_id,
                intent=None,
                confidence=None,
                products_extracted=0,
                order_created=False,
                order_id=None,
                continuation_order_id=None,
                processing_time_ms=0,
                error_message="AI processing failed - check logs for details"
            )
        
        # Handle different result types based on agent used
        order_created = False
        order_id = None
        continuation_order_id = None
        intent = None
        confidence = None
        products_extracted = 0
        processing_time_ms = 0
        
        # Check result type - could be SessionAnalysis or AutonomousResult
        if hasattr(result, 'execution_status'):  # AutonomousResult
            # Autonomous agent result
            logger.info(f"📊 Processed by Autonomous Agent")
            order_created = result.action_taken and result.action_taken.action_type == "create_order"
            if result.action_taken and hasattr(result.action_taken, 'result'):
                order_id = result.action_taken.result.get('order_id')
            processing_time_ms = result.processing_time_ms
            # Extract intent/confidence from decision if available
            if result.decision:
                intent = "BUY" if order_created else "UNKNOWN"
                confidence = result.decision.confidence if hasattr(result.decision, 'confidence') else 0.9
        elif hasattr(result, 'intent'):  # MessageAnalysis from streamlined agent
            # Streamlined agent result
            logger.info(f"📊 Processed by Streamlined Agent")
            intent = result.intent.intent
            confidence = result.intent.confidence
            products_extracted = len(result.extracted_products) if result.extracted_products else 0
            processing_time_ms = result.processing_time_ms
            
            # Check if order was created or continued
            if (result.intent.intent == "BUY" and 
                result.extracted_products and 
                result.is_high_confidence):
                order_created = True
            
            # Get order ID and continuation info from result
            continuation_order_id = None
            if hasattr(result, 'continuation_order_id') and result.continuation_order_id:
                continuation_order_id = result.continuation_order_id
                order_id = result.continuation_order_id  # Also set main order_id
                logger.info(f"📦 Order continued: {order_id}")
            elif hasattr(result, 'is_continuation') and result.is_continuation:
                logger.info(f"📦 Continuation detected but no order_id available")
        
        logger.info(f"✅ Message processed successfully: {request.message_id}")
        
        return MessageProcessingResponse(
            success=True,
            message_id=request.message_id,
            intent=intent,
            confidence=confidence,
            products_extracted=products_extracted,
            order_created=order_created,
            order_id=order_id,
            continuation_order_id=continuation_order_id,
            processing_time_ms=processing_time_ms,
            error_message=None
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing message {request.message_id}: {e}")
        
        return MessageProcessingResponse(
            success=False,
            message_id=request.message_id,
            intent=None,
            confidence=None,
            products_extracted=0,
            order_created=False,
            order_id=None,
            continuation_order_id=None,
            processing_time_ms=0,
            error_message=f"Processing error: {str(e)}"
        )


@app.post("/process-message-background")
async def process_message_background(
    request: MessageProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a message in the background and return immediately.
    
    Use this endpoint when you don't need to wait for processing results.
    Webhook responses can return faster this way.
    """
    
    logger.info(f"📨 Queuing background processing for message: {request.message_id}")
    
    if not agent_factory:
        raise HTTPException(
            status_code=503, 
            detail="Agent factory not initialized"
        )
    
    # Add to background tasks
    background_tasks.add_task(
        process_message_in_background,
        request
    )
    
    return {
        "success": True,
        "message": f"Message {request.message_id} queued for processing",
        "message_id": request.message_id
    }


async def process_message_in_background(request: MessageProcessingRequest):
    """Background task for message processing."""
    
    try:
        logger.info(f"🔄 Background processing message: {request.message_id}")
        
        # Use provided distributor_id or detect from environment
        distributor_id = request.distributor_id or get_current_distributor_id()
        
        # Create message object for processing (message already stored by webhook)
        message_data = {
            'id': request.message_id,
            'content': request.content,
            'customer_id': request.customer_id,
            'conversation_id': request.conversation_id,
            'channel': request.channel
        }
        
        # Process message using agent factory
        result = await agent_factory.process_message_with_best_agent(message_data)
        
        if result:
            # Log success based on result type
            if hasattr(result, 'execution_status'):  # Autonomous agent result
                logger.info(
                    f"✅ Background processing complete (Autonomous): {request.message_id} "
                    f"(status: {result.execution_status}, time: {result.processing_time_ms}ms)"
                )
            elif hasattr(result, 'intent'):  # Streamlined agent result
                logger.info(
                    f"✅ Background processing complete (Streamlined): {request.message_id} "
                    f"(intent: {result.intent.intent}, confidence: {result.intent.confidence:.2f})"
                )
            else:
                logger.info(f"✅ Background processing complete: {request.message_id}")
        else:
            logger.error(f"❌ Background processing failed: {request.message_id}")
            
    except Exception as e:
        logger.error(f"❌ Background processing error for {request.message_id}: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    
    return {
        "service": "Order Agent API",
        "version": "1.0.0",
        "description": "AI-powered customer message processing",
        "endpoints": {
            "health": "/health",
            "process_message": "/process-message",
            "process_background": "/process-message-background"
        },
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
        reload=False  # Disable in production
    )