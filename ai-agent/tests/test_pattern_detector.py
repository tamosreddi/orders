"""
Tests for Pattern Detector

Tests the pattern detection utilities for order intent, closing patterns, etc.

Run with: python -m pytest tests/test_pattern_detector.py -v
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pattern_detector import PatternDetector, PatternType, PatternMatch


class TestPatternDetector:
    """Test suite for PatternDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create PatternDetector instance."""
        return PatternDetector()
    
    def test_detector_initialization(self, detector):
        """Test that detector initializes with patterns."""
        assert detector.order_intent_patterns is not None
        assert detector.closing_patterns is not None
        assert detector.correction_patterns is not None
        assert len(detector.compiled_order_patterns['strong']) > 0
    
    def test_detect_order_intent_strong_spanish(self, detector):
        """Test detecting strong order intent in Spanish."""
        test_cases = [
            "Quiero 5 litros de leche",
            "Necesito 2 cajas de huevos", 
            "Dame 3 botellas de agua",
            "Envíame 10 paquetes de arroz"
        ]
        
        for text in test_cases:
            has_intent, confidence, matches = detector.detect_order_intent(text)
            assert has_intent is True
            assert confidence >= 0.5
            assert len(matches) > 0
    
    def test_detect_order_intent_strong_english(self, detector):
        """Test detecting strong order intent in English."""
        test_cases = [
            "I want 3 bottles of milk",
            "I need 2 boxes of eggs",
            "Give me 5 liters of water", 
            "Please send 4 packages of rice"
        ]
        
        for text in test_cases:
            has_intent, confidence, matches = detector.detect_order_intent(text)
            assert has_intent is True
            assert confidence >= 0.5
            assert len(matches) > 0
    
    def test_detect_order_intent_with_quantities(self, detector):
        """Test order intent detection with specific quantities."""
        text = "Necesito 5 kilos de azúcar y 3 litros de aceite"
        
        has_intent, confidence, matches = detector.detect_order_intent(text)
        
        assert has_intent is True
        assert confidence >= 0.7  # Should be high due to quantities + products
        
        # Should have both order intent and quantity matches
        intent_matches = [m for m in matches if m.pattern_type == PatternType.ORDER_INTENT]
        quantity_matches = [m for m in matches if m.pattern_type == PatternType.QUANTITY_MENTION]
        
        assert len(intent_matches) > 0
        assert len(quantity_matches) > 0
    
    def test_detect_order_intent_no_intent(self, detector):
        """Test messages without order intent."""
        test_cases = [
            "Hola, ¿cómo estás?",
            "Buenos días",
            "Gracias por la información",
            "¿Cuándo abren?",
            "Hello, how are you?"
        ]
        
        for text in test_cases:
            has_intent, confidence, matches = detector.detect_order_intent(text)
            # These should have low or no intent
            assert confidence < 0.8  # May have some weak signals but not strong
    
    def test_detect_closing_patterns_spanish(self, detector):
        """Test detecting closing patterns in Spanish."""
        test_cases = [
            "Eso es todo, gracias",
            "Sería todo por ahora", 
            "Nada más, confirma por favor",
            "Listo, envía la orden",
            "Ya está, muchas gracias"
        ]
        
        for text in test_cases:
            has_closing, confidence, matches = detector.detect_closing_patterns(text)
            assert has_closing is True
            assert confidence >= 0.6
            assert len(matches) > 0
    
    def test_detect_closing_patterns_english(self, detector):
        """Test detecting closing patterns in English."""
        test_cases = [
            "That's all, thank you",
            "That would be all for now",
            "Nothing else, please confirm",
            "Ready, send the order", 
            "Perfect, thanks!"
        ]
        
        for text in test_cases:
            has_closing, confidence, matches = detector.detect_closing_patterns(text)
            assert has_closing is True
            assert confidence >= 0.6
            assert len(matches) > 0
    
    def test_detect_corrections(self, detector):
        """Test detecting correction patterns."""
        test_cases = [
            "No, mejor quiero 5 en vez de 3",
            "Cambio la orden, son 8 cajas",
            "Me equivoqué, en realidad necesito 10",
            "Corrección: no quiero el aceite",
            "Actually, I want 5 instead of 3"
        ]
        
        for text in test_cases:
            has_correction, confidence, matches = detector.detect_corrections(text)
            assert has_correction is True
            assert confidence >= 0.7
            assert len(matches) > 0
    
    def test_extract_products_and_quantities(self, detector):
        """Test extracting structured product and quantity information."""
        test_cases = [
            {
                'text': "Quiero 5 litros de leche y 2 kilos de azúcar",
                'expected_items': 2
            },
            {
                'text': "Dame 3 botellas de agua",
                'expected_items': 1
            },
            {
                'text': "Necesito una docena de huevos",
                'expected_items': 1
            }
        ]
        
        for case in test_cases:
            items = detector.extract_products_and_quantities(case['text'])
            assert len(items) >= case['expected_items']
            
            # Check that each item has required fields
            for item in items:
                assert 'quantity' in item
                assert 'product_name' in item
                assert 'confidence' in item
                assert item['quantity'] > 0
    
    def test_analyze_message_context_order_message(self, detector):
        """Test comprehensive message analysis for order message."""
        text = "Hola, quiero 3 litros de leche y 2 kilos de azúcar, por favor"
        
        analysis = detector.analyze_message_context(text)
        
        assert analysis['has_order_intent'] is True
        assert analysis['overall_confidence'] >= 0.5
        assert analysis['suggested_action'] in ['START_OR_EXTEND_SESSION']
        assert len(analysis['extracted_items']) >= 2
        assert analysis['has_closing_pattern'] is False
    
    def test_analyze_message_context_closing_message(self, detector):
        """Test comprehensive message analysis for closing message."""
        text = "Eso sería todo por hoy, gracias"
        
        analysis = detector.analyze_message_context(text)
        
        assert analysis['has_closing_pattern'] is True
        assert analysis['suggested_action'] == 'CLOSE_SESSION'
        assert analysis['closing_confidence'] >= 0.6
    
    def test_analyze_message_context_correction_message(self, detector):
        """Test comprehensive message analysis for correction message."""
        text = "No, mejor cambio a 5 cajas en vez de 3"
        
        analysis = detector.analyze_message_context(text)
        
        assert analysis['has_correction'] is True
        assert analysis['suggested_action'] == 'MODIFY_SESSION'
        assert analysis['correction_confidence'] >= 0.7
    
    def test_should_start_session(self, detector):
        """Test session start decision logic."""
        # Should start session
        start_cases = [
            "Quiero 3 litros de leche",
            "Necesito 5 kilos de arroz",
            "Dame 2 botellas de aceite"
        ]
        
        for text in start_cases:
            should_start, confidence = detector.should_start_session(text)
            assert should_start is True
            assert confidence >= 0.5
        
        # Should not start session
        no_start_cases = [
            "Hola, ¿cómo estás?",
            "¿Cuánto cuesta la leche?",
            "Buenos días"
        ]
        
        for text in no_start_cases:
            should_start, confidence = detector.should_start_session(text)
            # These might have some intent but shouldn't have enough to start session
            if should_start:
                assert confidence < 0.7  # Low confidence if detected
    
    def test_should_close_session(self, detector):
        """Test session close decision logic."""
        # Should close session
        close_cases = [
            "Eso es todo, gracias",
            "Ya está, confirma por favor",
            "Nada más por ahora"
        ]
        
        for text in close_cases:
            should_close, confidence = detector.should_close_session(text)
            assert should_close is True
            assert confidence >= 0.6
        
        # Should not close session
        no_close_cases = [
            "También quiero 2 litros de aceite",
            "¿Tienes disponible azúcar?",
            "Hola, buenos días"
        ]
        
        for text in no_close_cases:
            should_close, confidence = detector.should_close_session(text)
            assert should_close is False
    
    def test_pattern_match_structure(self, detector):
        """Test that PatternMatch objects are structured correctly."""
        text = "Quiero 5 litros de leche"
        
        has_intent, confidence, matches = detector.detect_order_intent(text)
        
        for match in matches:
            assert isinstance(match, PatternMatch)
            assert hasattr(match, 'pattern_type')
            assert hasattr(match, 'confidence')
            assert hasattr(match, 'matched_text')
            assert hasattr(match, 'start_pos')
            assert hasattr(match, 'end_pos')
            assert hasattr(match, 'extracted_data')
            
            # Check that positions are valid
            assert match.start_pos >= 0
            assert match.end_pos > match.start_pos
            assert match.end_pos <= len(text)
    
    def test_multilingual_support(self, detector):
        """Test that detector works with both Spanish and English."""
        test_pairs = [
            ("Quiero 3 litros de leche", "I want 3 liters of milk"),
            ("Eso es todo, gracias", "That's all, thank you"),
            ("No, mejor 5 en vez de 3", "No, better 5 instead of 3")
        ]
        
        for spanish, english in test_pairs:
            # Test Spanish
            spanish_analysis = detector.analyze_message_context(spanish)
            
            # Test English  
            english_analysis = detector.analyze_message_context(english)
            
            # Both should have similar analysis results
            assert spanish_analysis['suggested_action'] == english_analysis['suggested_action']
            # Confidence might vary but both should be processed


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])