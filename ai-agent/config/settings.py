"""
Configuration settings for the Order Agent system.

Handles environment variable loading and validation following the pattern from
examples/example_pydantic_ai.py.
"""

from __future__ import annotations as _annotations

import os
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings with validation."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., min_length=1, description="OpenAI API key for LLM operations")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    
    # Supabase Configuration  
    supabase_url: str = Field(..., min_length=1, description="Supabase project URL")
    supabase_key: str = Field(..., min_length=1, description="Supabase API key")
    
    # Order Agent Configuration
    ai_confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum confidence threshold for auto-processing orders")
    max_processing_time_seconds: int = Field(default=30, ge=1, le=300, description="Maximum time to process a single message")
    batch_size: int = Field(default=10, ge=1, le=100, description="Number of messages to process in one batch")
    
    # Retry Configuration
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts for failed operations")
    retry_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0, description="Base delay between retries")
    
    # Database Configuration
    connection_pool_size: int = Field(default=5, ge=1, le=50, description="Database connection pool size")
    
    # HTTP API Configuration
    api_host: str = Field(default="0.0.0.0", description="Host for HTTP API server")
    api_port: int = Field(default=8001, ge=1000, le=65535, description="Port for HTTP API server")
    api_enabled: bool = Field(default=True, description="Enable HTTP API server for webhook integration")
    
    @validator('openai_api_key')
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format."""
        if not v.startswith('sk-'):
            raise ValueError('OpenAI API key must start with "sk-"')
        return v
    
    @validator('supabase_url')
    def validate_supabase_url(cls, v):
        """Validate Supabase URL format."""
        if not v.startswith('https://') or not v.endswith('.supabase.co'):
            raise ValueError('Supabase URL must be in format: https://project.supabase.co')
        return v

    class Config:
        """Pydantic configuration."""
        env_file = '.env'
        case_sensitive = False


def get_settings() -> Settings:
    """
    Get application settings with environment variable validation.
    
    Returns:
        Settings: Validated application settings
        
    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    try:
        return Settings(
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            openai_model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
            supabase_url=os.getenv('SUPABASE_PROJECT_URL', ''),
            supabase_key=os.getenv('SUPABASE_API_KEY', ''),
            ai_confidence_threshold=float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.8')),
            max_processing_time_seconds=int(os.getenv('MAX_PROCESSING_TIME_SECONDS', '30')),
            batch_size=int(os.getenv('BATCH_SIZE', '10')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            retry_delay_seconds=float(os.getenv('RETRY_DELAY_SECONDS', '1.0')),
            connection_pool_size=int(os.getenv('CONNECTION_POOL_SIZE', '5')),
            api_host=os.getenv('API_HOST', '0.0.0.0'),
            api_port=int(os.getenv('API_PORT', '8001')),
            api_enabled=os.getenv('API_ENABLED', 'true').lower() == 'true',
        )
    except Exception as e:
        raise ValueError(f"Failed to load settings: {e}")


# Global settings instance
settings = get_settings()