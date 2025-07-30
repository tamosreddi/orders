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
from agents.order_agent import create_streamlined_order_agent_processor, StreamlinedOrderProcessor

logger = logging.getLogger(__name__)

# Global variables for initialized components
database_service: Optional[DatabaseService] = None
order_agent_processor: Optional[StreamlinedOrderProcessor] = None


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
    global database_service, order_agent_processor
    
    logger.info("🚀 Starting Order Agent API...")
    
    try:
        # Initialize database service
        database_service = DatabaseService()
        logger.info("✅ Database service initialized")
        
        # Get distributor ID
        distributor_id = get_current_distributor_id()
        logger.info(f"🏢 Using distributor ID: {distributor_id}")
        
        # Create streamlined order agent processor (no complex product matching)
        order_agent_processor = create_streamlined_order_agent_processor(
            database_service,
            distributor_id
        )
        
        logger.info("🤖 Streamlined Order Agent processor initialized successfully")
        
        logger.info("🤖 Order Agent processor initialized successfully")
        
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
        "order_agent": "ok" if order_agent_processor else "not_initialized",
        "settings": "ok" if settings else "error"
    }
    
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
    
    if not order_agent_processor:
        logger.error("❌ Order agent processor not initialized")
        raise HTTPException(
            status_code=503, 
            detail="Order agent not initialized - check service health"
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
        
        # Check if processor is initialized
        if order_agent_processor is None:
            raise HTTPException(status_code=500, detail="Order agent processor not initialized")
        
        # Process message through the 6-step workflow
        analysis = await order_agent_processor.process_message(message_data)
        
        if not analysis:
            logger.error(f"❌ Failed to process message: {request.message_id}")
            return MessageProcessingResponse(
                success=False,
                message_id=request.message_id,
                intent=None,
                confidence=None,
                products_extracted=0,
                order_created=False,
                order_id=None,
                processing_time_ms=0,
                error_message="AI processing failed - check logs for details"
            )
        
        # Extract processing results
        order_created = False
        order_id = None
        
        # Check if order was created (high confidence BUY intent with products)
        if (analysis.intent.intent == "BUY" and 
            analysis.extracted_products and 
            analysis.is_high_confidence):
            order_created = True
            # Note: order_id would be returned from the processing if implemented
        
        logger.info(f"✅ Message processed successfully: {request.message_id}")
        
        return MessageProcessingResponse(
            success=True,
            message_id=request.message_id,
            intent=analysis.intent.intent,
            confidence=analysis.intent.confidence,
            products_extracted=len(analysis.extracted_products),
            order_created=order_created,
            order_id=order_id,
            processing_time_ms=analysis.processing_time_ms,
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
    
    if not order_agent_processor:
        raise HTTPException(
            status_code=503, 
            detail="Order agent not initialized"
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
        
        # Create message object for processing
        message_data = {
            'id': request.message_id,
            'content': request.content,
            'customer_id': request.customer_id,
            'conversation_id': request.conversation_id,
            'channel': request.channel
        }
        
        # Process message through AI workflow
        if order_agent_processor is None:
            raise HTTPException(status_code=500, detail="Order agent processor not initialized")
        
        analysis = await order_agent_processor.process_message(message_data)
        
        if analysis:
            intent = analysis.intent.intent
            confidence = analysis.intent.confidence
            products = len(analysis.extracted_products)
            logger.info(
                f"✅ Background processing complete: {request.message_id} "
                f"(intent: {intent}, confidence: {confidence:.2f}, products: {products})"
            )
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