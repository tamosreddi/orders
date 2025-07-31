"""
Unit tests for the Product Matcher module.

Tests all matching algorithms, confidence scoring, and question generation
to ensure reliable product identification for the AI agent.
"""

import pytest
import json
from typing import Dict, List, Any
from services.product_matcher import ProductMatcher, ProductMatch, MatchResult


class TestProductMatcher:
    """Test suite for ProductMatcher class."""
    
    @pytest.fixture
    def matcher(self):
        """Create ProductMatcher instance for testing."""
        return ProductMatcher()
    
    @pytest.fixture
    def sample_products(self) -> List[Dict[str, Any]]:
        """Sample product catalog for testing."""
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
                'common_misspellings': ['agau', 'aqua', 'agua emboteyada', 'boteyya']
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
                'common_misspellings': ['coca kola', 'koka', 'kola', 'kokacola']
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
                'common_misspellings': ['pesi', 'pepci', 'pepsy']
            },
            {
                'id': '4',
                'name': 'Leche Entera Pasteurizada 1L',
                'sku': 'DAI-LEC-ENT-1L',
                'unit': 'envase',
                'unit_price': 3.25,
                'stock_quantity': 200,
                'in_stock': True,
                'minimum_order_quantity': 6,
                'active': True,
                'brand': 'LaLechera',
                'category': 'Dairy',
                'size_variants': ['500ml', '1L', '2L'],
                'aliases': ['leche', 'milk', 'leche entera', 'leche fresca'],
                'keywords': ['leche', 'calcio', 'proteína', 'pasteurizada', 'fresca'],
                'ai_training_examples': ['quiero leche', 'necesito leche entera', 'dame 1 litro de leche', 'leche fresca'],
                'common_misspellings': ['lehe', 'leche enteera', 'lechee']
            },
            {
                'id': '5',
                'name': 'Papas Fritas Clásicas 150g',
                'sku': 'SNA-PAP-CLA-150',
                'unit': 'bolsa',
                'unit_price': 2.75,
                'stock_quantity': 0,  # Out of stock
                'in_stock': False,
                'minimum_order_quantity': 6,
                'active': True,
                'brand': 'CrunchySnacks',
                'category': 'Snacks',
                'size_variants': ['50g', '150g', '300g'],
                'aliases': ['papas', 'chips', 'papas fritas', 'frituras'],
                'keywords': ['papas', 'fritas', 'sal', 'crujientes', 'snack'],
                'ai_training_examples': ['quiero papas fritas', 'necesito chips', 'dame papas', 'frituras clásicas'],
                'common_misspellings': ['papas fritas', 'chips', 'papitas']
            }
        ]
    
    def test_normalize_text(self, matcher):
        """Test text normalization functionality."""
        # Basic normalization
        assert matcher.normalize_text("AGUA EMBOTELLADA") == "agua embotellada"
        assert matcher.normalize_text("  Coca  Cola  ") == "coca cola"
        
        # Remove noise words
        assert matcher.normalize_text("botella de agua") == "botella agua"
        assert matcher.normalize_text("refresco de cola") == "refresco cola"
        
        # Handle accents
        assert matcher.normalize_text("café molido") == "cafe molido"
        
        # Empty/None handling
        assert matcher.normalize_text("") == ""
        assert matcher.normalize_text(None) == ""
    
    def test_extract_product_terms(self, matcher):
        """Test product term extraction."""
        terms = matcher.extract_product_terms("quiero 5 botellas de agua")
        
        # Should include individual words
        assert "agua" in terms
        assert "botellas" in terms
        
        # Should include 2-word phrases
        assert "botellas agua" in terms
        
        # Should remove very short terms
        assert "de" not in terms
        
        # Should be unique
        assert len(terms) == len(set(terms))
    
    def test_fuzzy_similarity(self, matcher):
        """Test fuzzy similarity calculation."""
        # Exact match
        assert matcher.fuzzy_similarity("agua", "agua") == 1.0
        
        # Very similar
        similarity = matcher.fuzzy_similarity("coca", "coca cola")
        assert 0.5 < similarity < 1.0  # Adjusted threshold
        
        # Different
        similarity = matcher.fuzzy_similarity("agua", "leche")
        assert similarity < 0.5
        
        # Empty handling
        assert matcher.fuzzy_similarity("", "agua") == 0.0
        assert matcher.fuzzy_similarity(None, "agua") == 0.0
    
    def test_exact_name_matching(self, matcher, sample_products):
        """Test exact name matching."""
        query_terms = ["agua embotellada 500ml"]
        
        # Should find exact match
        match = matcher.match_exact_name(query_terms, sample_products[0])
        assert match is not None
        assert match.match_type == 'EXACT'
        assert match.confidence == 1.0
        assert match.product_name == 'Agua Embotellada 500ml'
        
        # Should not match different product
        match = matcher.match_exact_name(query_terms, sample_products[1])
        assert match is None
    
    def test_alias_matching(self, matcher, sample_products):
        """Test alias matching."""
        query_terms = ["agua"]
        
        # Should match via alias
        match = matcher.match_aliases(query_terms, sample_products[0])
        assert match is not None
        assert match.match_type == 'ALIAS_EXACT'
        assert match.confidence == 0.95
        assert match.matched_text == "agua"
        
        # Should not match product without matching alias
        match = matcher.match_aliases(query_terms, sample_products[1])
        assert match is None
    
    def test_keyword_matching(self, matcher, sample_products):
        """Test keyword matching."""
        # Extract normalized terms like the matcher does
        query_terms = matcher.extract_product_terms("hidratación")
        
        # Should match via keyword
        match = matcher.match_keywords(query_terms, sample_products[0])
        assert match is not None
        assert match.match_type == 'KEYWORD_EXACT'
        assert match.confidence == 0.85
        
        # Multiple keywords should boost confidence
        query_terms = matcher.extract_product_terms("hidratación botella")
        match = matcher.match_keywords(query_terms, sample_products[0])
        assert match.confidence > 0.85
    
    def test_ai_training_matching(self, matcher, sample_products):
        """Test AI training examples matching."""
        # Should match similar training example
        match = matcher.match_ai_training_examples("quiero agua", sample_products[0])
        assert match is not None
        assert match.match_type == 'AI_TRAINING'
        assert match.confidence > 0.7
        
        # Should not match dissimilar query
        match = matcher.match_ai_training_examples("necesito zapatos", sample_products[0])
        assert match is None
    
    def test_misspelling_matching(self, matcher, sample_products):
        """Test common misspellings matching."""
        query_terms = ["agau"]  # Common misspelling of "agua"
        
        # Should match misspelling
        match = matcher.match_common_misspellings(query_terms, sample_products[0])
        assert match is not None
        assert match.match_type == 'MISSPELLING'
        assert match.confidence == 0.90
    
    def test_fuzzy_matching(self, matcher, sample_products):
        """Test fuzzy matching."""
        query_terms = ["cocacola"]  # Close to "coca cola"
        
        # Should match with fuzzy logic
        match = matcher.match_fuzzy(query_terms, sample_products[1])
        assert match is not None
        assert match.match_type in ['FUZZY_HIGH', 'FUZZY_MEDIUM', 'FUZZY_LOW']
        assert 0.4 <= match.confidence <= 1.0
    
    def test_skip_inactive_products(self, matcher, sample_products):
        """Test that inactive/out-of-stock products are skipped."""
        query_terms = ["papas"]
        
        # Should skip out-of-stock product
        matches = matcher.find_product_matches("papas", sample_products)
        
        # Should not include the out-of-stock papas fritas
        product_ids = [m.product_id for m in matches]
        assert '5' not in product_ids  # Product 5 is out of stock
    
    def test_confidence_classification(self, matcher):
        """Test confidence level classification."""
        # High confidence match
        high_match = ProductMatch(
            product_id='1', product_name='Test', sku='TEST', unit='unit',
            unit_price=1.0, stock_quantity=10, in_stock=True, minimum_order_quantity=1,
            match_type='EXACT', confidence=0.95, matched_text='test', original_query='test'
        )
        assert matcher.classify_confidence_level([high_match]) == "HIGH"
        
        # Medium confidence match
        medium_match = ProductMatch(
            product_id='1', product_name='Test', sku='TEST', unit='unit',
            unit_price=1.0, stock_quantity=10, in_stock=True, minimum_order_quantity=1,
            match_type='FUZZY_MEDIUM', confidence=0.70, matched_text='test', original_query='test'
        )
        assert matcher.classify_confidence_level([medium_match]) == "MEDIUM"
        
        # Low confidence match
        low_match = ProductMatch(
            product_id='1', product_name='Test', sku='TEST', unit='unit',
            unit_price=1.0, stock_quantity=10, in_stock=True, minimum_order_quantity=1,
            match_type='FUZZY_LOW', confidence=0.50, matched_text='test', original_query='test'
        )
        assert matcher.classify_confidence_level([low_match]) == "LOW"
        
        # No matches
        assert matcher.classify_confidence_level([]) == "NONE"
    
    def test_question_generation(self, matcher, sample_products):
        """Test clarifying question generation."""
        # High confidence - no question needed
        high_match = ProductMatch(
            product_id='1', product_name='Agua Embotellada 500ml', sku='TEST', unit='botella',
            unit_price=1.5, stock_quantity=10, in_stock=True, minimum_order_quantity=1,
            match_type='EXACT', confidence=0.95, matched_text='agua', original_query='agua',
            size_variants=['500ml', '1L']
        )
        question = matcher.generate_clarifying_question("agua", [high_match])
        assert question is None
        
        # Medium confidence with size variants
        medium_match = ProductMatch(
            product_id='1', product_name='Agua Embotellada 500ml', sku='TEST', unit='botella',
            unit_price=1.5, stock_quantity=10, in_stock=True, minimum_order_quantity=1,
            match_type='FUZZY_MEDIUM', confidence=0.70, matched_text='agua', original_query='agua',
            size_variants=['500ml', '1L']
        )
        question = matcher.generate_clarifying_question("agua", [medium_match])
        assert question is not None
        assert "500ml" in question and "1L" in question
        
        # Multiple matches
        matches = [
            ProductMatch(
                product_id='1', product_name='Coca Cola 350ml', sku='TEST1', unit='lata',
                unit_price=2.25, stock_quantity=10, in_stock=True, minimum_order_quantity=1,
                match_type='FUZZY_MEDIUM', confidence=0.70, matched_text='cola', original_query='cola'
            ),
            ProductMatch(
                product_id='2', product_name='Pepsi 500ml', sku='TEST2', unit='botella',
                unit_price=2.50, stock_quantity=10, in_stock=True, minimum_order_quantity=1,
                match_type='FUZZY_MEDIUM', confidence=0.65, matched_text='cola', original_query='cola'
            )
        ]
        question = matcher.generate_clarifying_question("cola", matches)
        assert question is not None
        assert "Coca Cola" in question and "Pepsi" in question
        
        # No matches
        question = matcher.generate_clarifying_question("producto inexistente", [])
        assert question is not None
        assert "No encontré" in question
    
    def test_full_matching_workflow(self, matcher, sample_products):
        """Test complete matching workflow."""
        # Test high confidence match
        result = matcher.match_products("agua", sample_products)
        assert result.confidence_level == "HIGH"
        assert result.best_match is not None
        assert result.best_match.product_name == "Agua Embotellada 500ml"
        assert not result.requires_clarification
        assert result.suggested_question is None
        assert result.processing_time_ms >= 0  # Can be 0 for very fast operations
        
        # Test medium confidence match
        result = matcher.match_products("cola", sample_products)
        assert result.confidence_level in ["HIGH", "MEDIUM"]  # Could be either depending on matching
        assert len(result.matches) >= 1
        
        # Test no matches
        result = matcher.match_products("producto inexistente", sample_products)
        assert result.confidence_level == "NONE"
        assert len(result.matches) == 0
        assert result.requires_clarification
        assert result.suggested_question is not None
    
    def test_performance(self, matcher, sample_products):
        """Test that matching completes within reasonable time."""
        import time
        
        start_time = time.time()
        result = matcher.match_products("agua embotellada", sample_products)
        end_time = time.time()
        
        # Should complete within 500ms
        processing_time = (end_time - start_time) * 1000
        assert processing_time < 500
        
        # Internal timing should be reasonable
        assert result.processing_time_ms < 100  # Very fast for small catalog
    
    def test_edge_cases(self, matcher, sample_products):
        """Test edge cases and error handling."""
        # Empty query
        result = matcher.match_products("", sample_products)
        assert result.confidence_level == "NONE"
        assert len(result.matches) == 0
        
        # None query
        result = matcher.match_products(None, sample_products)
        assert result.confidence_level == "NONE"
        
        # Empty catalog
        result = matcher.match_products("agua", [])
        assert result.confidence_level == "NONE"
        
        # None catalog
        result = matcher.match_products("agua", None)
        assert result.confidence_level == "NONE"
        
        # Very long query
        long_query = "quiero " + "agua " * 100
        result = matcher.match_products(long_query, sample_products)
        assert result.processing_time_ms < 1000  # Should still be fast
    
    def test_sort_by_confidence(self, matcher, sample_products):
        """Test that matches are sorted by confidence."""
        result = matcher.match_products("refresco", sample_products)
        
        if len(result.matches) > 1:
            confidences = [m.confidence for m in result.matches]
            # Should be sorted in descending order
            assert confidences == sorted(confidences, reverse=True)


# Integration test with actual data types
class TestProductMatcherIntegration:
    """Integration tests for ProductMatcher with realistic scenarios."""
    
    @pytest.fixture
    def matcher(self):
        return ProductMatcher()
    
    def test_spanish_queries(self, matcher):
        """Test with Spanish language queries."""
        products = [
            {
                'id': '1', 'name': 'Agua Embotellada 500ml', 'sku': 'W1', 'unit': 'botella',
                'unit_price': 1.50, 'stock_quantity': 100, 'in_stock': True, 'minimum_order_quantity': 1,
                'active': True, 'brand': 'AquaPura', 'category': 'Beverages',
                'aliases': ['agua', 'water'], 'keywords': ['hidratación', 'bebida'],
                'ai_training_examples': ['quiero agua', 'necesito agua'], 'common_misspellings': ['agau']
            }
        ]
        
        test_queries = [
            "quiero 5 botellas de agua",
            "necesito agua para la oficina",
            "¿tienes agua embotellada?",
            "dame agau por favor"  # misspelling
        ]
        
        for query in test_queries:
            result = matcher.match_products(query, products)
            assert result.confidence_level in ["HIGH", "MEDIUM"]
            assert len(result.matches) >= 1
    
    def test_quantity_extraction_ignored(self, matcher):
        """Test that quantities in queries don't affect matching."""
        products = [
            {
                'id': '1', 'name': 'Coca Cola 350ml', 'sku': 'C1', 'unit': 'lata',
                'unit_price': 2.25, 'stock_quantity': 100, 'in_stock': True, 'minimum_order_quantity': 1,
                'active': True, 'brand': 'Coca Cola', 'category': 'Beverages',
                'aliases': ['coca', 'cola'], 'keywords': ['refresco'], 'ai_training_examples': ['quiero coca'],
                'common_misspellings': []
            }
        ]
        
        queries_with_quantities = [
            "quiero 1 coca cola",
            "necesito 12 latas de coca",
            "dame 50 cocas",
            "quiero coca cola x10"
        ]
        
        for query in queries_with_quantities:
            result = matcher.match_products(query, products)
            assert result.confidence_level in ["HIGH", "MEDIUM"]
            assert result.best_match.product_name == "Coca Cola 350ml"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])