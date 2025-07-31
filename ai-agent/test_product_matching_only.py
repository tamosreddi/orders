#!/usr/bin/env python3
"""
Test script for the product matching functionality only (no database).

Tests the ProductMatcher with our mock catalog data.
"""

import asyncio
import logging
from services.product_matcher import ProductMatcher
from schemas.message import ExtractedProduct

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mock_catalog():
    """Create mock catalog data for testing."""
    return [
        {
            'id': '1',
            'name': 'Agua Embotellada 500ml',
            'sku': 'BEV-WAT-500',
            'unit': 'botella',
            'unit_price': 1.50,
            'stock_quantity': 500,
            'in_stock': True,
            'minimum_order_quantity': 12,
            'active': True,
            'brand': 'AquaPura',
            'category': 'Beverages',
            'size_variants': ['500ml', '1L', '1.5L'],
            'aliases': ['agua', 'water', 'botella de agua', 'agua pura', 'h2o'],
            'keywords': ['agua', 'hidratación', 'purificada', 'botella', 'bebida'],
            'ai_training_examples': ['quiero agua', 'necesito botellas de agua', 'dame agua embotellada', '5 aguas por favor'],
            'common_misspellings': ['agau', 'aqua', 'agua emboteyada', 'boteyya'],
            'seasonal_patterns': []
        },
        {
            'id': '2',
            'name': 'Coca Cola 350ml',
            'sku': 'BEV-COL-350',
            'unit': 'lata',
            'unit_price': 2.25,
            'stock_quantity': 300,
            'in_stock': True,
            'minimum_order_quantity': 6,
            'active': True,
            'brand': 'Coca Cola',
            'category': 'Beverages',
            'size_variants': ['350ml', '500ml', '1L', '2L'],
            'aliases': ['coca', 'cola', 'coca cola', 'coke', 'refresco de cola'],
            'keywords': ['cola', 'refresco', 'gaseosa', 'lata', 'coca'],
            'ai_training_examples': ['quiero coca cola', 'dame una cola', 'necesito refrescos', 'coca 350ml'],
            'common_misspellings': ['coca kola', 'koka', 'kola', 'kokacola'],
            'seasonal_patterns': []
        },
        {
            'id': '3',
            'name': 'Pepsi 500ml',
            'sku': 'BEV-PEP-500',
            'unit': 'botella',
            'unit_price': 2.50,
            'stock_quantity': 200,
            'in_stock': True,
            'minimum_order_quantity': 6,
            'active': True,
            'brand': 'Pepsi',
            'category': 'Beverages',
            'size_variants': ['350ml', '500ml', '1L', '2L'],
            'aliases': ['pepsi', 'cola pepsi', 'refresco pepsi'],
            'keywords': ['pepsi', 'cola', 'refresco', 'gaseosa', 'botella'],
            'ai_training_examples': ['quiero pepsi', 'dame una pepsi', 'pepsi de 500ml', 'refresco pepsi'],
            'common_misspellings': ['pesi', 'pepci', 'pepsy'],
            'seasonal_patterns': []
        }
    ]


def test_product_matching():
    """Test the product matching functionality."""
    
    logger.info("🧪 Testing ProductMatcher with mock catalog")
    
    # Create matcher and catalog
    matcher = ProductMatcher()
    catalog = create_mock_catalog()
    
    # Test cases
    test_cases = [
        {
            'query': 'agua',
            'expected_confidence': 'HIGH',
            'description': 'Exact alias match'
        },
        {
            'query': 'quiero agua embotellada',
            'expected_confidence': 'HIGH',
            'description': 'AI training example match'
        },
        {
            'query': 'cola',
            'expected_confidence': 'HIGH',
            'description': 'Multiple alias matches - should pick best'
        },
        {
            'query': 'refrescos',
            'expected_confidence': 'MEDIUM',
            'description': 'Keyword match requiring clarification'
        },
        {
            'query': 'agau',
            'expected_confidence': 'HIGH',
            'description': 'Common misspelling match'
        },
        {
            'query': 'zapatos',
            'expected_confidence': 'NONE',
            'description': 'No match - product not in catalog'
        }
    ]
    
    logger.info(f"Running {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected = test_case['expected_confidence']
        description = test_case['description']
        
        logger.info(f"\n🧪 Test {i}: {description}")
        logger.info(f"Query: '{query}'")
        
        # Run the matcher
        result = matcher.match_products(query, catalog)
        
        # Log results
        logger.info(f"Confidence Level: {result.confidence_level}")
        logger.info(f"Matches Found: {len(result.matches)}")
        
        if result.best_match:
            logger.info(f"Best Match: {result.best_match.product_name} (confidence: {result.best_match.confidence:.2f})")
        
        if result.suggested_question:
            logger.info(f"Suggested Question: {result.suggested_question}")
        
        # Check if result matches expectation
        if result.confidence_level == expected:
            logger.info("✅ Test passed!")
        else:
            logger.warning(f"⚠️ Expected {expected}, got {result.confidence_level}")
        
        logger.info(f"Processing Time: {result.processing_time_ms}ms")
    
    logger.info("\n🎉 Product matching tests completed!")


if __name__ == "__main__":
    test_product_matching()