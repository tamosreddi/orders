"""
Main application entry point for the Order Agent system.

Runs the Order Agent with async processing loop, following the pattern from
examples/example_pydantic_ai_mcp.py with asyncio.run().
"""

from __future__ import annotations as _annotations

import asyncio
import logging
import signal
import sys
from typing import Dict, Any
from contextlib import asynccontextmanager

from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('order_agent.log') if not sys.stdout.isatty() else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_flag
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True


class OrderAgentMain:
    """
    Streamlined Order Agent - HTTP API only.
    
    Simplified for pilot: no polling, no complex initialization.
    """
    
    def __init__(self):
        """Initialize the main application."""
        logger.info("OrderAgentMain initialized (HTTP-only mode)")
    
    async def start_http_api(self) -> None:
        """
        Start the HTTP API server for webhook integration.
        
        Runs concurrently with the polling loop to handle real-time requests.
        """
        if not settings.api_enabled:
            logger.info("HTTP API disabled - skipping API server startup")
            return
        
        try:
            import uvicorn
            from api import app
            
            logger.info(f"Starting HTTP API server on {settings.api_host}:{settings.api_port}")
            
            # Configure uvicorn server
            config = uvicorn.Config(
                app=app,
                host=settings.api_host,
                port=settings.api_port,
                log_level="info",
                access_log=False,  # Reduce noise in logs
                reload=False  # Disable in production
            )
            
            server = uvicorn.Server(config)
            
            # Run server until shutdown signal
            await server.serve()
            
        except ImportError:
            logger.error("FastAPI/uvicorn not installed - HTTP API unavailable")
            logger.info("Install with: pip install fastapi uvicorn")
        except Exception as e:
            logger.error(f"Failed to start HTTP API server: {e}")
            # Don't raise - allow polling loop to continue
    
    async def run(self) -> None:
        """
        Run the HTTP API server only (no polling loop).
        """
        try:
            # Start HTTP API server
            if settings.api_enabled:
                logger.info("🚀 Starting HTTP API server only (streamlined mode)")
                await self.start_http_api()
            else:
                logger.error("HTTP API is disabled - nothing to run!")
                return
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error in main application: {e}")
        finally:
            logger.info("Order Agent shutdown completed")


async def main():
    """
    Main entry point.
    
    PATTERN: Use asyncio.run() like examples/example_pydantic_ai_mcp.py
    """
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=== Order Agent Starting (Streamlined Mode) ===")
    logger.info(f"Configuration: {settings.openai_model} model")
    
    if settings.api_enabled:
        logger.info(f"HTTP API: Enabled on {settings.api_host}:{settings.api_port}")
    else:
        logger.error("HTTP API: Disabled - Agent will not function!")
    
    # Create and run the application
    app = OrderAgentMain()
    await app.run()
    
    logger.info("=== Order Agent Stopped ===")


if __name__ == "__main__":
    # CRITICAL: Use virtual environment 'venv_linux' must be used for all Python execution
    # PATTERN: Concurrent HTTP API + polling loop architecture
    asyncio.run(main())