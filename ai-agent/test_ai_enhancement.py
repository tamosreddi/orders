#!/usr/bin/env python3
"""
Simple test script for AI Enhancement feature in ProductMatcher.

Tests the new AI-enhanced product matching with sample data.
"""

import asyncio
import logging
from services.product_matcher import ProductMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample product catalog for testing
SAMPLE_CATALOG = [
    {
        'id': '1',
        'name': 'Agua Embotellada 500ml',
        'sku': 'AGUA-500',
        'unit': 'botella',
        'unit_price': 15.0,
        'stock_quantity': 100,
        'in_stock': True,
        'minimum_order_quantity': 1,
        'active': True,
        'brand': 'AquaPura',
        'category': 'Bebidas',
        'size_variants': ['500ml'],
        'aliases': ['agua chica', 'botella pequeña'],
        'keywords': ['agua', 'hidratación', 'bebida'],
        'ai_training_examples': ['agua pequeña', 'botellita de agua'],
        'common_misspellings': ['aga', 'agua'],
        'seasonal_patterns': []
    },
    {
        'id': '2',
        'name': 'Agua Embotellada 1.5L',
        'sku': 'AGUA-1500',
        'unit': 'botella',
        'unit_price': 25.0,
        'stock_quantity': 50,
        'in_stock': True,
        'minimum_order_quantity': 1,
        'active': True,
        'brand': 'AquaPura',
        'category': 'Bebidas',
        'size_variants': ['1.5L'],
        'aliases': ['agua grande', 'botella grande'],
        'keywords': ['agua', 'hidratación', 'bebida', 'familiar'],
        'ai_training_examples': ['agua familiar', 'botella grande de agua'],
        'common_misspellings': ['aga grande'],
        'seasonal_patterns': []
    },
    {
        'id': '3',
        'name': 'Aceite de Canola 1L',
        'sku': 'ACEITE-CANOLA-1L',
        'unit': 'botella',
        'unit_price': 85.0,
        'stock_quantity': 30,
        'in_stock': True,
        'minimum_order_quantity': 1,
        'active': True,
        'brand': 'CocinaFácil',
        'category': 'Aceites',
        'size_variants': ['1L'],
        'aliases': ['canola', 'aceite para cocinar'],
        'keywords': ['aceite', 'cocinar', 'freír', 'canola'],
        'ai_training_examples': ['aceite para freír', 'canola para cocina'],
        'common_misspellings': ['acite', 'cánola'],
        'seasonal_patterns': []
    }
]

# Test cases that should trigger AI enhancement
TEST_CASES = [
    "botella grande de agua",  # Should match 1.5L water
    "agua familiar",           # Should match 1.5L water  
    "aceite para freír",       # Should match canola oil
    "agua chica",              # Should match 500ml water
    "algo para cocinar",       # Vague - should get LOW confidence
]

async def test_ai_enhancement():
    """Test AI enhancement functionality."""
    
    logger.info("🧪 Testing AI Enhancement for ProductMatcher")
    logger.info("=" * 50)
    
    # Initialize matcher
    matcher = ProductMatcher()
    
    for i, test_query in enumerate(TEST_CASES, 1):
        logger.info(f"\n🔍 Test {i}: '{test_query}'")
        logger.info("-" * 30)
        
        try:
            # Run the matching with AI enhancement
            result = await matcher.match_products(test_query, SAMPLE_CATALOG)
            
            logger.info(f"Confidence Level: {result.confidence_level}")
            
            if result.best_match:
                logger.info(f"Best Match: {result.best_match.product_name}")
                logger.info(f"Match Type: {result.best_match.match_type}")
                logger.info(f"Confidence: {result.best_match.confidence:.2f}")
                logger.info(f"Matched Text: {result.best_match.matched_text}")
            else:
                logger.info("No match found")
            
            if result.requires_clarification:
                logger.info(f"Clarification: {result.suggested_question}")
            
            logger.info(f"Processing Time: {result.processing_time_ms}ms")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info("🎯 AI Enhancement test completed!")

if __name__ == "__main__":
    asyncio.run(test_ai_enhancement())