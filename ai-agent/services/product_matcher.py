"""
Intelligent Product Matching Engine for AI Agent

This module provides sophisticated product matching capabilities that enable
the AI agent to match customer product requests against the product catalog
with various levels of confidence and precision.

Key Features:
- Multi-level matching algorithms (exact, alias, fuzzy, AI training)
- Confidence scoring system
- Question generation for uncertain matches
- Performance optimized for real-time usage
"""

from __future__ import annotations as _annotations

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import unicodedata

logger = logging.getLogger(__name__)


@dataclass
class ProductMatch:
    """Represents a product match with confidence scoring."""
    
    product_id: str
    product_name: str
    sku: str
    unit: str
    unit_price: float
    stock_quantity: int
    in_stock: bool
    minimum_order_quantity: int
    
    # Matching metadata
    match_type: str  # EXACT, ALIAS, KEYWORD, FUZZY, AI_TRAINING, MISSPELLING
    confidence: float  # 0.0 to 1.0
    matched_text: str  # What text matched
    original_query: str  # Original customer query
    
    # Additional product info for validation
    brand: Optional[str] = None
    category: str = ""
    size_variants: List[str] = None
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.size_variants is None:
            self.size_variants = []
        if self.aliases is None:
            self.aliases = []


@dataclass
class MatchResult:
    """Result of product matching operation."""
    
    query: str
    matches: List[ProductMatch]
    best_match: Optional[ProductMatch]
    confidence_level: str  # HIGH, MEDIUM, LOW, NONE
    requires_clarification: bool
    suggested_question: Optional[str] = None
    processing_time_ms: int = 0


class ProductMatcher:
    """
    Intelligent product matching engine with multi-level algorithms.
    
    Provides various matching strategies with confidence scoring to help
    AI agents make informed decisions about product identification.
    """
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.60
    
    # Match type confidence scores
    MATCH_CONFIDENCE_SCORES = {
        'EXACT': 1.0,
        'ALIAS_EXACT': 0.95,
        'MISSPELLING': 0.90,
        'KEYWORD_EXACT': 0.85,
        'AI_TRAINING': 0.80,
        'FUZZY_HIGH': 0.75,
        'FUZZY_MEDIUM': 0.60,
        'FUZZY_LOW': 0.45,
        'PARTIAL': 0.40
    }
    
    def __init__(self):
        """Initialize the product matcher."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent matching.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text suitable for matching
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove accents and special characters
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise words for product matching
        noise_words = ['de', 'del', 'la', 'el', 'un', 'una', 'por', 'para', 'con']
        words = text.split()
        words = [w for w in words if w not in noise_words]
        
        return ' '.join(words)
    
    def extract_product_terms(self, query: str) -> List[str]:
        """
        Extract potential product terms from customer query.
        
        Args:
            query: Customer query text
            
        Returns:
            List of potential product terms
        """
        normalized = self.normalize_text(query)
        
        # Split into words and phrases
        words = normalized.split()
        terms = []
        
        # Add individual words
        terms.extend(words)
        
        # Add 2-word phrases
        for i in range(len(words) - 1):
            terms.append(f"{words[i]} {words[i + 1]}")
            
        # Add 3-word phrases for compound product names
        for i in range(len(words) - 2):
            terms.append(f"{words[i]} {words[i + 1]} {words[i + 2]}")
        
        # Remove very short terms
        terms = [t for t in terms if len(t) > 2]
        
        return list(set(terms))  # Remove duplicates
    
    def fuzzy_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate fuzzy similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
            
        # Normalize both texts
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        if norm1 == norm2:
            return 1.0
            
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def match_exact_name(self, query_terms: List[str], product: Dict[str, Any]) -> Optional[ProductMatch]:
        """
        Try exact name matching.
        
        Args:
            query_terms: Extracted terms from customer query
            product: Product dictionary from database
            
        Returns:
            ProductMatch if found, None otherwise
        """
        product_name = self.normalize_text(product['name'])
        
        for term in query_terms:
            if term == product_name:
                return ProductMatch(
                    product_id=product['id'],
                    product_name=product['name'],
                    sku=product['sku'],
                    unit=product['unit'],
                    unit_price=float(product['unit_price']),
                    stock_quantity=product['stock_quantity'],
                    in_stock=product['in_stock'],
                    minimum_order_quantity=product['minimum_order_quantity'],
                    match_type='EXACT',
                    confidence=self.MATCH_CONFIDENCE_SCORES['EXACT'],
                    matched_text=term,
                    original_query=' '.join(query_terms),
                    brand=product.get('brand'),
                    category=product.get('category', ''),
                    size_variants=product.get('size_variants', []),
                    aliases=product.get('aliases', [])
                )
        
        return None
    
    def match_aliases(self, query_terms: List[str], product: Dict[str, Any]) -> Optional[ProductMatch]:
        """
        Try alias matching.
        
        Args:
            query_terms: Extracted terms from customer query
            product: Product dictionary from database
            
        Returns:
            ProductMatch if found, None otherwise
        """
        aliases = product.get('aliases', [])
        if not aliases:
            return None
            
        for term in query_terms:
            for alias in aliases:
                if term == self.normalize_text(alias):
                    return ProductMatch(
                        product_id=product['id'],
                        product_name=product['name'],
                        sku=product['sku'],
                        unit=product['unit'],
                        unit_price=float(product['unit_price']),
                        stock_quantity=product['stock_quantity'],
                        in_stock=product['in_stock'],
                        minimum_order_quantity=product['minimum_order_quantity'],
                        match_type='ALIAS_EXACT',
                        confidence=self.MATCH_CONFIDENCE_SCORES['ALIAS_EXACT'],
                        matched_text=term,
                        original_query=' '.join(query_terms),
                        brand=product.get('brand'),
                        category=product.get('category', ''),
                        size_variants=product.get('size_variants', []),
                        aliases=product.get('aliases', [])
                    )
        
        return None
    
    def match_keywords(self, query_terms: List[str], product: Dict[str, Any]) -> Optional[ProductMatch]:
        """
        Try keyword matching.
        
        Args:
            query_terms: Extracted terms from customer query
            product: Product dictionary from database
            
        Returns:
            ProductMatch if found, None otherwise
        """
        keywords = product.get('keywords', [])
        if not keywords:
            return None
            
        matched_keywords = []
        for term in query_terms:
            for keyword in keywords:
                if term == self.normalize_text(keyword):
                    matched_keywords.append(term)
        
        if matched_keywords:
            # Higher confidence if multiple keywords match
            confidence_boost = min(0.1 * (len(matched_keywords) - 1), 0.15)
            confidence = self.MATCH_CONFIDENCE_SCORES['KEYWORD_EXACT'] + confidence_boost
            
            return ProductMatch(
                product_id=product['id'],
                product_name=product['name'],
                sku=product['sku'],
                unit=product['unit'],
                unit_price=float(product['unit_price']),
                stock_quantity=product['stock_quantity'],
                in_stock=product['in_stock'],
                minimum_order_quantity=product['minimum_order_quantity'],
                match_type='KEYWORD_EXACT',
                confidence=min(confidence, 1.0),
                matched_text=', '.join(matched_keywords),
                original_query=' '.join(query_terms),
                brand=product.get('brand'),
                category=product.get('category', ''),
                size_variants=product.get('size_variants', []),
                aliases=product.get('aliases', [])
            )
        
        return None
    
    def match_ai_training_examples(self, query: str, product: Dict[str, Any]) -> Optional[ProductMatch]:
        """
        Try AI training examples matching.
        
        Args:
            query: Original customer query
            product: Product dictionary from database
            
        Returns:
            ProductMatch if found, None otherwise
        """
        training_examples = product.get('ai_training_examples', [])
        if not training_examples:
            return None
            
        normalized_query = self.normalize_text(query)
        
        best_similarity = 0.0
        best_example = ""
        
        for example in training_examples:
            similarity = self.fuzzy_similarity(normalized_query, example)
            if similarity > best_similarity:
                best_similarity = similarity
                best_example = example
        
        # Require high similarity for training examples
        if best_similarity >= 0.7:
            return ProductMatch(
                product_id=product['id'],
                product_name=product['name'],
                sku=product['sku'],
                unit=product['unit'],
                unit_price=float(product['unit_price']),
                stock_quantity=product['stock_quantity'],
                in_stock=product['in_stock'],
                minimum_order_quantity=product['minimum_order_quantity'],
                match_type='AI_TRAINING',
                confidence=self.MATCH_CONFIDENCE_SCORES['AI_TRAINING'] * best_similarity,
                matched_text=best_example,
                original_query=query,
                brand=product.get('brand'),
                category=product.get('category', ''),
                size_variants=product.get('size_variants', []),
                aliases=product.get('aliases', [])
            )
        
        return None
    
    def match_common_misspellings(self, query_terms: List[str], product: Dict[str, Any]) -> Optional[ProductMatch]:
        """
        Try common misspellings matching.
        
        Args:
            query_terms: Extracted terms from customer query
            product: Product dictionary from database
            
        Returns:
            ProductMatch if found, None otherwise
        """
        misspellings = product.get('common_misspellings', [])
        if not misspellings:
            return None
            
        for term in query_terms:
            for misspelling in misspellings:
                if term == self.normalize_text(misspelling):
                    return ProductMatch(
                        product_id=product['id'],
                        product_name=product['name'],
                        sku=product['sku'],
                        unit=product['unit'],
                        unit_price=float(product['unit_price']),
                        stock_quantity=product['stock_quantity'],
                        in_stock=product['in_stock'],
                        minimum_order_quantity=product['minimum_order_quantity'],
                        match_type='MISSPELLING',
                        confidence=self.MATCH_CONFIDENCE_SCORES['MISSPELLING'],
                        matched_text=term,
                        original_query=' '.join(query_terms),
                        brand=product.get('brand'),
                        category=product.get('category', ''),
                        size_variants=product.get('size_variants', []),
                        aliases=product.get('aliases', [])
                    )
        
        return None
    
    def match_fuzzy(self, query_terms: List[str], product: Dict[str, Any]) -> Optional[ProductMatch]:
        """
        Try fuzzy matching against product name and aliases.
        
        Args:
            query_terms: Extracted terms from customer query
            product: Product dictionary from database
            
        Returns:
            ProductMatch if found, None otherwise
        """
        # Collect all searchable text for this product
        searchable_texts = [product['name']]
        if product.get('aliases'):
            searchable_texts.extend(product['aliases'])
        if product.get('brand'):
            searchable_texts.append(product['brand'])
        
        best_similarity = 0.0
        best_matched_text = ""
        best_query_term = ""
        
        for term in query_terms:
            for text in searchable_texts:
                similarity = self.fuzzy_similarity(term, text)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_matched_text = text
                    best_query_term = term
        
        # Determine match type and confidence based on similarity
        if best_similarity >= 0.85:
            match_type = 'FUZZY_HIGH'
        elif best_similarity >= 0.65:
            match_type = 'FUZZY_MEDIUM'
        elif best_similarity >= 0.45:
            match_type = 'FUZZY_LOW'
        else:
            return None  # Too low similarity
        
        confidence = self.MATCH_CONFIDENCE_SCORES[match_type] * best_similarity
        
        return ProductMatch(
            product_id=product['id'],
            product_name=product['name'],
            sku=product['sku'],
            unit=product['unit'],
            unit_price=float(product['unit_price']),
            stock_quantity=product['stock_quantity'],
            in_stock=product['in_stock'],
            minimum_order_quantity=product['minimum_order_quantity'],
            match_type=match_type,
            confidence=confidence,
            matched_text=f"{best_query_term} → {best_matched_text}",
            original_query=' '.join(query_terms),
            brand=product.get('brand'),
            category=product.get('category', ''),
            size_variants=product.get('size_variants', []),
            aliases=product.get('aliases', [])
        )
    
    def find_product_matches(self, query: str, product_catalog: List[Dict[str, Any]]) -> List[ProductMatch]:
        """
        Find all possible product matches for a query.
        
        Args:
            query: Customer product query
            product_catalog: List of product dictionaries
            
        Returns:
            List of ProductMatch objects sorted by confidence
        """
        if not query or not product_catalog:
            return []
        
        matches = []
        query_terms = self.extract_product_terms(query)
        
        self.logger.debug(f"Matching query '{query}' with terms: {query_terms}")
        
        for product in product_catalog:
            # Skip inactive or out-of-stock products
            if not product.get('active', True) or not product.get('in_stock', True):
                continue
            
            # Try each matching algorithm in order of preference
            match = None
            
            # 1. Exact name match (highest confidence)
            match = self.match_exact_name(query_terms, product)
            if match:
                matches.append(match)
                continue
            
            # 2. Alias match
            match = self.match_aliases(query_terms, product)
            if match:
                matches.append(match)
                continue
            
            # 3. Common misspellings
            match = self.match_common_misspellings(query_terms, product)
            if match:
                matches.append(match)
                continue
            
            # 4. Keyword match
            match = self.match_keywords(query_terms, product)
            if match:
                matches.append(match)
                continue
            
            # 5. AI training examples
            match = self.match_ai_training_examples(query, product)
            if match:
                matches.append(match)
                continue
            
            # 6. Fuzzy match (lowest confidence)
            match = self.match_fuzzy(query_terms, product)
            if match:
                matches.append(match)
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda m: m.confidence, reverse=True)
        
        self.logger.debug(f"Found {len(matches)} matches for '{query}'")
        
        return matches
    
    def classify_confidence_level(self, matches: List[ProductMatch]) -> str:
        """
        Classify the overall confidence level of matches.
        
        Args:
            matches: List of product matches
            
        Returns:
            Confidence level: HIGH, MEDIUM, LOW, or NONE
        """
        if not matches:
            return "NONE"
        
        best_match = matches[0]
        
        if best_match.confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "HIGH"
        elif best_match.confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"
    
    def generate_clarifying_question(self, query: str, matches: List[ProductMatch]) -> Optional[str]:
        """
        Generate clarifying question for uncertain matches.
        
        Args:
            query: Original customer query
            matches: List of potential matches
            
        Returns:
            Clarifying question string or None
        """
        if not matches:
            return f"No encontré '{query}' en nuestro catálogo. ¿Podrías describir mejor el producto que necesitas?"
        
        confidence_level = self.classify_confidence_level(matches)
        
        if confidence_level == "HIGH":
            return None  # No question needed for high confidence
        
        # Get top 3 matches for questions
        top_matches = matches[:3]
        
        if confidence_level == "MEDIUM":
            if len(top_matches) == 1:
                match = top_matches[0]
                if match.size_variants and len(match.size_variants) > 1:
                    variants = ', '.join(match.size_variants)
                    return f"¿Te refieres a {match.product_name}? Tenemos disponible en: {variants}"
                else:
                    return f"¿Te refieres a {match.product_name}?"
            else:
                # Multiple similar matches
                names = [m.product_name for m in top_matches]
                if len(names) == 2:
                    return f"¿Te refieres a {names[0]} o {names[1]}?"
                else:
                    options = ', '.join(names[:-1]) + f" o {names[-1]}"
                    return f"¿Te refieres a {options}?"
        
        elif confidence_level == "LOW":
            # Try to understand what category they're looking for
            categories = list(set(m.category for m in top_matches if m.category))
            if categories:
                if len(categories) == 1:
                    return f"¿Buscas algo específico en {categories[0].lower()}? Tenemos varios productos disponibles."
                else:
                    cat_list = ', '.join(categories[:-1]) + f" o {categories[-1].lower()}"
                    return f"¿Buscas algo en {cat_list}?"
            else:
                return f"¿Podrías ser más específico sobre '{query}'? No estoy seguro de qué producto necesitas."
        
        return None
    
    def match_products(self, query: str, product_catalog: List[Dict[str, Any]]) -> MatchResult:
        """
        Main method to match products with comprehensive result.
        
        Args:
            query: Customer product query
            product_catalog: List of product dictionaries from database
            
        Returns:
            MatchResult with matches and recommendations
        """
        import time
        start_time = time.time() * 1000  # Convert to milliseconds
        
        matches = self.find_product_matches(query, product_catalog)
        confidence_level = self.classify_confidence_level(matches)
        
        best_match = matches[0] if matches else None
        requires_clarification = confidence_level in ["MEDIUM", "LOW", "NONE"]
        suggested_question = None
        
        if requires_clarification:
            suggested_question = self.generate_clarifying_question(query, matches)
        
        processing_time = int(time.time() * 1000 - start_time)
        
        result = MatchResult(
            query=query,
            matches=matches,
            best_match=best_match,
            confidence_level=confidence_level,
            requires_clarification=requires_clarification,
            suggested_question=suggested_question,
            processing_time_ms=processing_time
        )
        
        self.logger.info(
            f"Product matching complete: query='{query}', "
            f"matches={len(matches)}, confidence={confidence_level}, "
            f"time={processing_time}ms"
        )
        
        return result