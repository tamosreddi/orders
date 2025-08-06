"""
Pattern Detection Utilities for Order Session Management

This module provides utilities to detect various patterns in customer messages:
- Order intent detection
- Closing patterns
- Correction patterns
- Product mentions

Author: AI Assistant
Date: 2025-08-04
"""

import re
import logging
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be detected."""
    ORDER_INTENT = "ORDER_INTENT"
    CLOSING_PATTERN = "CLOSING_PATTERN"
    CORRECTION_PATTERN = "CORRECTION_PATTERN"
    QUANTITY_MENTION = "QUANTITY_MENTION"
    PRODUCT_MENTION = "PRODUCT_MENTION"
    GREETING = "GREETING"
    QUESTION = "QUESTION"


@dataclass
class PatternMatch:
    """Represents a detected pattern in text."""
    pattern_type: PatternType
    confidence: float
    matched_text: str
    start_pos: int
    end_pos: int
    extracted_data: Dict[str, Any]


class PatternDetector:
    """
    Detects various patterns in customer messages for order processing.
    
    This class uses regex patterns and keyword matching to identify
    different types of customer intents and behaviors.
    """
    
    def __init__(self):
        """Initialize the pattern detector with predefined patterns."""
        self._load_patterns()
    
    def _load_patterns(self):
        """Load all pattern definitions."""
        
        # Order intent patterns (Spanish and English)
        self.order_intent_patterns = {
            # Strong intent indicators
            "strong": [
                r"\b(quiero|necesito|dame|pídeme|ordeno|envíame|mándame)\b",
                r"\b(i want|i need|give me|send me|order|i'll take)\b",
                r"\b(me das|me traes|me vendes|me mandas)\b",
                r"\b(can you send|could you send|please send)\b",
                r"\b(voy a pedir|quiero pedir|necesito pedir)\b",
                r"\b(going to order|want to order|need to order)\b"
            ],
            # Medium intent indicators
            "medium": [
                r"\b(\d+)\s*(de|of|x)?\s*([a-záéíóúñ\w\s]+)",  # Numbers with items
                r"\b(cuánto|precio|cuesta|cost|price|how much)\b.*\b(de|of|for)\b",
                r"\b(disponible|available|tienes|do you have)\b",
                r"\b(me interesa|estoy interesado|interested in)\b"
            ],
            # Weak intent indicators
            "weak": [
                r"\b(hola|hi|hello|buenos días|good morning)\b",
                r"\b(gracias|thanks|thank you)\b"
            ]
        }
        
        # Closing patterns
        self.closing_patterns = [
            r"\b(eso es todo|that's all|that's it|nada más|nothing else)\b",
            r"\b(sería todo|would be all|eso sería todo)\b",
            r"\b(gracias|thanks|thank you|muchas gracias)\b",
            r"\b(confirma|confirm|confirmado|confirmed)\b",
            r"\b(listo|ready|ok|okay|perfecto|perfect)\b",
            r"\b(envía|send it|mándalo|go ahead)\b",
            r"\b(ya está|that's done|terminamos|we're done)\b"
        ]
        
        # Correction patterns
        self.correction_patterns = [
            r"\b(no[,\s]+(mejor|actually|en realidad|instead))\b",
            r"\b(cambio|change|corrección|correction|rectificación)\b",
            r"\b(en vez de|instead of|mejor que|rather than)\b",
            r"\b(me equivoqué|i made a mistake|error|wrong)\b",
            r"\b(no quiero|i don't want|cancel|cancela)\b",
            r"\b(son|it's|serían|would be)\s+(\d+)",  # Quantity corrections
        ]
        
        # Quantity patterns
        self.quantity_patterns = [
            r"\b(\d+(?:\.\d+)?)\s*(kilos?|kg|gramos?|gr?|libras?|lbs?)\b",
            r"\b(\d+(?:\.\d+)?)\s*(litros?|lt?|mililitros?|ml)\b",
            r"\b(\d+(?:\.\d+)?)\s*(cajas?|boxes?|paquetes?|packages?)\b",
            r"\b(\d+(?:\.\d+)?)\s*(botellas?|bottles?|envases?|containers?)\b",
            r"\b(\d+(?:\.\d+)?)\s*(unidades?|units?|piezas?|pieces?)\b",
            r"\b(\d+(?:\.\d+)?)\s*(docenas?|dozens?)\b",
            r"(\d+(?:\.\d+)?)\s*([a-záéíóúñ\w\s]+)",  # Generic number + item
        ]
        
        # Product mention patterns
        self.product_patterns = [
            # Beverages
            r"\b(coca cola|coke|pepsi|sprite|fanta|agua|water|jugo|juice|cerveza|beer)\b",
            # Food items
            r"\b(pan|bread|leche|milk|queso|cheese|huevos|eggs|arroz|rice|frijol|beans)\b",
            # Snacks
            r"\b(papas|chips|galletas|cookies|dulces|candy|chocolate)\b",
            # General categories
            r"\b(comida|food|bebida|drink|snack|botana)\b"
        ]
        
        # Compile regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        self.compiled_order_patterns = {}
        for strength, patterns in self.order_intent_patterns.items():
            self.compiled_order_patterns[strength] = [
                re.compile(pattern, re.IGNORECASE | re.UNICODE) 
                for pattern in patterns
            ]
        
        self.compiled_closing_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE) 
            for pattern in self.closing_patterns
        ]
        
        self.compiled_correction_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE) 
            for pattern in self.correction_patterns
        ]
        
        self.compiled_quantity_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE) 
            for pattern in self.quantity_patterns
        ]
        
        self.compiled_product_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE) 
            for pattern in self.product_patterns
        ]
    
    def detect_order_intent(self, text: str) -> Tuple[bool, float, List[PatternMatch]]:
        """
        Detect if a message contains order intent.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Tuple of (has_intent, confidence_score, matches)
        """
        matches = []
        total_confidence = 0.0
        
        # Check strong intent patterns (confidence: 0.8-0.9)
        for pattern in self.compiled_order_patterns["strong"]:
            for match in pattern.finditer(text):
                pattern_match = PatternMatch(
                    pattern_type=PatternType.ORDER_INTENT,
                    confidence=0.85,
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    extracted_data={"strength": "strong", "pattern": pattern.pattern}
                )
                matches.append(pattern_match)
                total_confidence += 0.85
        
        # Check medium intent patterns (confidence: 0.5-0.7)
        for pattern in self.compiled_order_patterns["medium"]:
            for match in pattern.finditer(text):
                pattern_match = PatternMatch(
                    pattern_type=PatternType.ORDER_INTENT,
                    confidence=0.6,
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    extracted_data={"strength": "medium", "pattern": pattern.pattern}
                )
                matches.append(pattern_match)
                total_confidence += 0.6
        
        # Check for quantity + product combinations (high confidence for orders)
        quantity_matches = self._detect_quantities(text)
        product_matches = self._detect_products(text)
        
        if quantity_matches and product_matches:
            # High confidence when we have both quantities and products
            total_confidence += 0.8
            matches.extend(quantity_matches)
            matches.extend(product_matches)
        
        # Normalize confidence score
        final_confidence = min(total_confidence, 1.0) if matches else 0.0
        has_intent = final_confidence >= 0.5
        
        logger.debug(f"Order intent detection: {has_intent} (confidence: {final_confidence:.2f}) in '{text[:50]}...'")
        
        return has_intent, final_confidence, matches
    
    def detect_closing_patterns(self, text: str) -> Tuple[bool, float, List[PatternMatch]]:
        """
        Detect if a message contains closing patterns.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Tuple of (has_closing, confidence_score, matches)
        """
        matches = []
        
        for pattern in self.compiled_closing_patterns:
            for match in pattern.finditer(text):
                pattern_match = PatternMatch(
                    pattern_type=PatternType.CLOSING_PATTERN,
                    confidence=0.8,
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    extracted_data={"pattern": pattern.pattern}
                )
                matches.append(pattern_match)
        
        # Calculate confidence based on number and quality of matches
        confidence = min(len(matches) * 0.8, 1.0) if matches else 0.0
        has_closing = confidence >= 0.6
        
        logger.debug(f"Closing pattern detection: {has_closing} (confidence: {confidence:.2f}) in '{text[:50]}...'")
        
        return has_closing, confidence, matches
    
    def detect_corrections(self, text: str) -> Tuple[bool, float, List[PatternMatch]]:
        """
        Detect if a message contains correction patterns.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Tuple of (has_correction, confidence_score, matches)
        """
        matches = []
        
        for pattern in self.compiled_correction_patterns:
            for match in pattern.finditer(text):
                pattern_match = PatternMatch(
                    pattern_type=PatternType.CORRECTION_PATTERN,
                    confidence=0.9,
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    extracted_data={"pattern": pattern.pattern}
                )
                matches.append(pattern_match)
        
        confidence = min(len(matches) * 0.9, 1.0) if matches else 0.0
        has_correction = confidence >= 0.7
        
        logger.debug(f"Correction pattern detection: {has_correction} (confidence: {confidence:.2f}) in '{text[:50]}...'")
        
        return has_correction, confidence, matches
    
    def _detect_quantities(self, text: str) -> List[PatternMatch]:
        """Detect quantity mentions in text."""
        matches = []
        
        for pattern in self.compiled_quantity_patterns:
            for match in pattern.finditer(text):
                groups = match.groups()
                quantity = groups[0]
                unit = groups[1] if len(groups) > 1 else "units"
                
                pattern_match = PatternMatch(
                    pattern_type=PatternType.QUANTITY_MENTION,
                    confidence=0.8,
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    extracted_data={
                        "quantity": quantity,
                        "unit": unit,
                        "pattern": pattern.pattern
                    }
                )
                matches.append(pattern_match)
        
        return matches
    
    def _detect_products(self, text: str) -> List[PatternMatch]:
        """Detect product mentions in text."""
        matches = []
        
        for pattern in self.compiled_product_patterns:
            for match in pattern.finditer(text):
                pattern_match = PatternMatch(
                    pattern_type=PatternType.PRODUCT_MENTION,
                    confidence=0.7,
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    extracted_data={"product": match.group(), "pattern": pattern.pattern}
                )
                matches.append(pattern_match)
        
        return matches
    
    def extract_products_and_quantities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract structured product and quantity information from text.
        
        Args:
            text: The message text to analyze
            
        Returns:
            List of dictionaries with product and quantity information
        """
        extracted_items = []
        
        # Look for quantity + product patterns
        combined_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*(kilos?|kg|gramos?|gr?|libras?|lbs?|litros?|lt?|mililitros?|ml|cajas?|boxes?|paquetes?|packages?|botellas?|bottles?|envases?|containers?|unidades?|units?|piezas?|pieces?|docenas?|dozens?|de|x)?\s*([a-záéíóúñ\w\s]+)",
            re.IGNORECASE | re.UNICODE
        )
        
        for match in combined_pattern.finditer(text):
            quantity = match.group(1)
            unit = match.group(2) or "units"
            product = match.group(3).strip()
            
            # Clean up product name
            product = re.sub(r'\s+', ' ', product)  # Normalize whitespace
            product = product.lower()
            
            # Skip if product name is too short or generic
            if len(product) < 3 or product in ['de', 'x', 'y', 'and', 'con', 'with']:
                continue
            
            extracted_item = {
                "quantity": float(quantity),
                "unit": unit,
                "product_name": product,
                "confidence": 0.8,
                "original_text": match.group(),
                "position": (match.start(), match.end())
            }
            
            extracted_items.append(extracted_item)
        
        logger.debug(f"Extracted {len(extracted_items)} items from '{text[:50]}...'")
        
        return extracted_items
    
    def analyze_message_context(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a message.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "original_text": text,
            "has_order_intent": False,
            "has_closing_pattern": False,
            "has_correction": False,
            "extracted_items": [],
            "overall_confidence": 0.0,
            "suggested_action": "NONE",
            "all_matches": []
        }
        
        # Detect order intent
        has_intent, intent_confidence, intent_matches = self.detect_order_intent(text)
        analysis["has_order_intent"] = has_intent
        analysis["order_intent_confidence"] = intent_confidence
        analysis["all_matches"].extend(intent_matches)
        
        # Detect closing patterns
        has_closing, closing_confidence, closing_matches = self.detect_closing_patterns(text)
        analysis["has_closing_pattern"] = has_closing
        analysis["closing_confidence"] = closing_confidence
        analysis["all_matches"].extend(closing_matches)
        
        # Detect corrections
        has_correction, correction_confidence, correction_matches = self.detect_corrections(text)
        analysis["has_correction"] = has_correction
        analysis["correction_confidence"] = correction_confidence
        analysis["all_matches"].extend(correction_matches)
        
        # Extract products and quantities
        analysis["extracted_items"] = self.extract_products_and_quantities(text)
        
        # Calculate overall confidence
        total_confidence = intent_confidence
        if analysis["extracted_items"]:
            total_confidence += 0.3  # Boost for having concrete items
        
        analysis["overall_confidence"] = min(total_confidence, 1.0)
        
        # Suggest action based on analysis
        if has_closing and analysis["overall_confidence"] > 0.5:
            analysis["suggested_action"] = "CLOSE_SESSION"
        elif has_correction:
            analysis["suggested_action"] = "MODIFY_SESSION"
        elif has_intent or analysis["extracted_items"]:
            analysis["suggested_action"] = "START_OR_EXTEND_SESSION"
        else:
            analysis["suggested_action"] = "NONE"
        
        return analysis
    
    def should_start_session(self, text: str) -> Tuple[bool, float]:
        """
        Determine if a message should start a new order session.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Tuple of (should_start, confidence_score)
        """
        analysis = self.analyze_message_context(text)
        
        should_start = (
            analysis["has_order_intent"] and 
            analysis["overall_confidence"] >= 0.5 and
            len(analysis["extracted_items"]) > 0
        )
        
        return should_start, analysis["overall_confidence"]
    
    def should_close_session(self, text: str) -> Tuple[bool, float]:
        """
        Determine if a message should close an active order session.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Tuple of (should_close, confidence_score)
        """
        analysis = self.analyze_message_context(text)
        
        should_close = (
            analysis["has_closing_pattern"] and 
            analysis["closing_confidence"] >= 0.6
        )
        
        return should_close, analysis["closing_confidence"]