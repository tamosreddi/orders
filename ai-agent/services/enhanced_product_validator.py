"""
Enhanced Product Validation Service with Human Validation Flags.

This service extends the product validation logic from order_agent.py with
enhanced handling for unknown, uncertain, or problematic products by adding
"HUMAN VALIDATION REQUESTED" flags.

Key Features:
- Same validation mechanism as order_agent.py
- HUMAN VALIDATION REQUESTED flags for unknown products
- Enhanced confidence scoring
- Detailed validation notes for human review
- Integration with existing ProductMatcher service
"""

from __future__ import annotations as _annotations

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from services.database import DatabaseService
from services.product_matcher import ProductMatcher, MatchResult
from schemas.message import ExtractedProduct
from tools.supabase_tools import fetch_product_catalog

logger = logging.getLogger(__name__)


class ValidationFlag(Enum):
    """Product validation flags for human review."""
    VALIDATED = "validated"
    HUMAN_VALIDATION_REQUESTED = "human_validation_requested"  
    UNCERTAIN_MATCH = "uncertain_match"
    NO_CATALOG_MATCH = "no_catalog_match"
    PRICING_UNKNOWN = "pricing_unknown"
    OUT_OF_STOCK = "out_of_stock"
    MINIMUM_ORDER_NOT_MET = "minimum_order_not_met"


@dataclass
class ValidationResult:
    """Result of enhanced product validation."""
    validated_products: List[ExtractedProduct]
    requires_human_validation: bool
    human_validation_flags: List[ValidationFlag]
    validation_summary: str
    suggested_questions: List[str]
    confidence_score: float  # Overall validation confidence


@dataclass
class ProductValidationIssue:
    """Detailed information about a product validation issue."""
    product_name: str
    issue_type: ValidationFlag
    description: str
    suggested_action: str
    catalog_alternatives: List[str] = None
    
    def __post_init__(self):
        if self.catalog_alternatives is None:
            self.catalog_alternatives = []


class EnhancedProductValidator:
    """
    Enhanced product validation service with human validation flags.
    
    Extends the validation logic from order_agent.py with enhanced handling
    for edge cases, unknown products, and situations requiring human review.
    """
    
    def __init__(self, database: DatabaseService, distributor_id: str):
        self.database = database
        self.distributor_id = distributor_id  
        self.product_matcher = ProductMatcher()
        
        # Confidence thresholds for validation decisions
        self.high_confidence_threshold = 0.85
        self.medium_confidence_threshold = 0.60
        self.low_confidence_threshold = 0.30
        
        logger.info(f"Initialized EnhancedProductValidator for distributor {distributor_id}")
    
    async def validate_products_with_flags(
        self,
        extracted_products: List[ExtractedProduct],
        original_message: str,
        conversation_id: str
    ) -> ValidationResult:
        """
        Enhanced product validation with human validation flags.
        
        Args:
            extracted_products: Products extracted from message
            original_message: Original customer message
            conversation_id: Conversation ID for context
            
        Returns:
            ValidationResult with enhanced flags and human validation indicators
        """
        logger.info(f"🔍 Enhanced validation for {len(extracted_products)} products")
        
        if not extracted_products:
            return ValidationResult(
                validated_products=[],
                requires_human_validation=False,
                human_validation_flags=[],
                validation_summary="No products to validate",
                suggested_questions=[],
                confidence_score=1.0
            )
        
        try:
            # Get product catalog (same as order_agent.py)
            catalog_models = await fetch_product_catalog(
                self.database, self.distributor_id, active_only=True
            )
            
            if not catalog_models:
                return await self._handle_no_catalog_scenario(extracted_products)
            
            # Convert catalog models to dictionaries (same as order_agent.py)
            catalog_dicts = await self._convert_catalog_to_dicts(catalog_models)
            
            # Validate each product with enhanced logic
            validated_products = []
            validation_issues = []
            overall_flags = set()
            suggested_questions = []
            confidence_scores = []
            
            for product in extracted_products:
                result = await self._validate_single_product_enhanced(
                    product, catalog_dicts, original_message
                )
                
                validated_products.append(result['product'])
                validation_issues.extend(result['issues'])
                overall_flags.update(result['flags'])
                suggested_questions.extend(result['questions'])
                confidence_scores.append(result['confidence'])
            
            # Calculate overall validation metrics
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            requires_human_validation = ValidationFlag.HUMAN_VALIDATION_REQUESTED in overall_flags
            
            # Generate validation summary
            validation_summary = await self._generate_validation_summary(
                validation_issues, overall_confidence
            )
            
            logger.info(
                f"✅ Enhanced validation complete: "
                f"{len(validated_products)} products, "
                f"confidence: {overall_confidence:.2f}, "
                f"human validation needed: {requires_human_validation}"
            )
            
            return ValidationResult(
                validated_products=validated_products,
                requires_human_validation=requires_human_validation,
                human_validation_flags=list(overall_flags),
                validation_summary=validation_summary,
                suggested_questions=suggested_questions[:3],  # Limit to 3 questions
                confidence_score=overall_confidence
            )
            
        except Exception as e:
            logger.error(f"Enhanced product validation failed: {e}")
            return await self._handle_validation_error(extracted_products, str(e))
    
    async def _validate_single_product_enhanced(
        self,
        product: ExtractedProduct,
        catalog_dicts: List[Dict[str, Any]],
        original_message: str
    ) -> Dict[str, Any]:
        """Enhanced validation for a single product with detailed flags."""
        
        # Use the same product matcher as order_agent.py
        match_result = self.product_matcher.match_products(
            product.product_name, catalog_dicts
        )
        
        issues = []
        flags = set()
        questions = []
        confidence = product.confidence or 0.5
        
        logger.info(
            f"Product '{product.product_name}': "
            f"confidence_level={match_result.confidence_level}, "
            f"matches={len(match_result.matches)}"
        )
        
        # CASE 1: HIGH confidence match (same as order_agent.py)
        if match_result.confidence_level == "HIGH":
            best_match = match_result.best_match
            product.status = "confirmed"
            product.matched_product_id = best_match.product_id
            product.matched_product_name = best_match.product_name
            product.validation_notes = f"High confidence match ({best_match.confidence:.0%})"
            flags.add(ValidationFlag.VALIDATED)
            
            # Update unit if catalog has better info
            if best_match.unit and not product.unit:
                product.unit = best_match.unit
                
            # Check for additional validation requirements
            catalog_product = next(
                (p for p in catalog_dicts if p['id'] == best_match.product_id), None
            )
            if catalog_product:
                await self._check_additional_requirements(
                    product, catalog_product, issues, flags, questions
                )
            
            confidence = max(confidence, best_match.confidence)
            
        # CASE 2: MEDIUM confidence match - Enhanced handling
        elif match_result.confidence_level == "MEDIUM":
            best_match = match_result.best_match
            product.status = "pending"
            product.matched_product_id = best_match.product_id if best_match else None
            product.matched_product_name = best_match.product_name if best_match else None
            
            # Enhanced validation for medium confidence
            if best_match and best_match.confidence >= 0.7:
                # Higher end of medium - ask for confirmation
                product.validation_notes = f"Good match but needs confirmation ({best_match.confidence:.0%})"
                flags.add(ValidationFlag.UNCERTAIN_MATCH)
                questions.append(
                    f"¿Te refieres a '{best_match.product_name}' cuando mencionas '{product.product_name}'?"
                )
            else:
                # Lower end of medium - request human validation
                product.validation_notes = f"Uncertain match requires human review ({best_match.confidence:.0%} confidence)"
                flags.add(ValidationFlag.HUMAN_VALIDATION_REQUESTED)
                
                issues.append(ProductValidationIssue(
                    product_name=product.product_name,
                    issue_type=ValidationFlag.UNCERTAIN_MATCH,
                    description=f"Product match confidence is moderate ({best_match.confidence:.0%})",
                    suggested_action="Human should verify the correct product",
                    catalog_alternatives=[best_match.product_name] if best_match else []
                ))
            
            confidence = best_match.confidence if best_match else 0.5
            
        # CASE 3: LOW confidence match - Enhanced handling  
        elif match_result.confidence_level == "LOW":
            product.status = "pending"
            flags.add(ValidationFlag.HUMAN_VALIDATION_REQUESTED)
            
            if match_result.best_match:
                best_match = match_result.best_match
                product.matched_product_id = best_match.product_id
                product.matched_product_name = best_match.product_name
                product.validation_notes = f"Low confidence match requires human validation ({best_match.confidence:.0%})"
                
                # Provide alternatives for human review
                alternatives = [
                    match.product_name for match in match_result.matches[:3]
                ]
                
                issues.append(ProductValidationIssue(
                    product_name=product.product_name,
                    issue_type=ValidationFlag.UNCERTAIN_MATCH,
                    description=f"Low confidence match ({best_match.confidence:.0%})",
                    suggested_action="Human should select correct product from alternatives",
                    catalog_alternatives=alternatives
                ))
                
                questions.append(
                    f"No estoy seguro sobre '{product.product_name}'. "
                    f"¿Te refieres a alguno de estos: {', '.join(alternatives[:2])}?"
                )
                
                confidence = best_match.confidence
            else:
                product.validation_notes = "Very low confidence, needs human review"
                confidence = 0.2
                
        # CASE 4: NO match - Enhanced handling with human validation
        else:  # NONE
            product.status = "pending"
            product.validation_notes = "No catalog match found - HUMAN VALIDATION REQUESTED"
            flags.add(ValidationFlag.HUMAN_VALIDATION_REQUESTED)
            flags.add(ValidationFlag.NO_CATALOG_MATCH)
            
            issues.append(ProductValidationIssue(
                product_name=product.product_name,
                issue_type=ValidationFlag.NO_CATALOG_MATCH,
                description="Product not found in catalog",
                suggested_action="Human should identify correct product or add to catalog",
                catalog_alternatives=await self._get_similar_products(product.product_name, catalog_dicts)
            ))
            
            # Suggest similar products if available
            similar_products = await self._get_similar_products(product.product_name, catalog_dicts)
            if similar_products:
                questions.append(
                    f"No encuentro '{product.product_name}' en nuestro catálogo. "
                    f"¿Te refieres a alguno de estos: {', '.join(similar_products[:2])}?"
                )
            else:
                questions.append(
                    f"'{product.product_name}' no está en nuestro catálogo. "
                    "¿Puedes describir mejor el producto que necesitas?"
                )
            
            confidence = 0.1
        
        return {
            'product': product,
            'issues': issues,
            'flags': flags,
            'questions': questions,
            'confidence': confidence
        }
    
    async def _check_additional_requirements(
        self,
        product: ExtractedProduct,
        catalog_product: Dict[str, Any],
        issues: List[ProductValidationIssue],
        flags: set,
        questions: List[str]
    ) -> None:
        """Check additional requirements like stock, pricing, minimum orders."""
        
        # Check stock availability
        if not catalog_product.get('in_stock', True):
            flags.add(ValidationFlag.OUT_OF_STOCK)
            flags.add(ValidationFlag.HUMAN_VALIDATION_REQUESTED)
            
            issues.append(ProductValidationIssue(
                product_name=product.product_name,
                issue_type=ValidationFlag.OUT_OF_STOCK,
                description="Product is currently out of stock",
                suggested_action="Human should confirm availability or suggest alternatives"
            ))
            
            questions.append(
                f"'{product.product_name}' está agotado actualmente. "
                "¿Te interesa un producto similar o prefieres esperar?"
            )
        
        # Check minimum order quantity
        min_qty = catalog_product.get('minimum_order_quantity', 1)
        if product.quantity < min_qty:
            flags.add(ValidationFlag.MINIMUM_ORDER_NOT_MET)
            flags.add(ValidationFlag.HUMAN_VALIDATION_REQUESTED)
            
            issues.append(ProductValidationIssue(
                product_name=product.product_name,
                issue_type=ValidationFlag.MINIMUM_ORDER_NOT_MET,
                description=f"Quantity {product.quantity} is below minimum order of {min_qty}",
                suggested_action=f"Increase quantity to {min_qty} or confirm exception"
            ))
            
            questions.append(
                f"El pedido mínimo para '{product.product_name}' es {min_qty} unidades. "
                f"¿Quieres {min_qty} unidades?"
            )
        
        # Check pricing availability
        if not catalog_product.get('unit_price') or catalog_product.get('unit_price', 0) <= 0:
            flags.add(ValidationFlag.PRICING_UNKNOWN)
            flags.add(ValidationFlag.HUMAN_VALIDATION_REQUESTED)
            
            issues.append(ProductValidationIssue(
                product_name=product.product_name,
                issue_type=ValidationFlag.PRICING_UNKNOWN,
                description="Product pricing not available",
                suggested_action="Human should provide current pricing"
            ))
    
    async def _get_similar_products(
        self, product_name: str, catalog_dicts: List[Dict[str, Any]], limit: int = 3
    ) -> List[str]:
        """Find similar products in catalog for suggestions."""
        try:
            # Simple similarity based on common words
            product_words = set(product_name.lower().split())
            similarities = []
            
            for catalog_item in catalog_dicts:
                catalog_name = catalog_item.get('name', '').lower()
                catalog_words = set(catalog_name.split())
                
                # Calculate simple word overlap similarity
                common_words = product_words.intersection(catalog_words)
                if common_words:
                    similarity = len(common_words) / len(product_words.union(catalog_words))
                    similarities.append((catalog_item['name'], similarity))
            
            # Sort by similarity and return top matches
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [name for name, _ in similarities[:limit] if _ > 0.1]
            
        except Exception as e:
            logger.warning(f"Could not find similar products: {e}")
            return []
    
    async def _convert_catalog_to_dicts(self, catalog_models) -> List[Dict[str, Any]]:
        """Convert catalog models to dictionaries (same as order_agent.py)."""
        catalog_dicts = []
        for product in catalog_models:
            catalog_dicts.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'unit': product.unit,
                'unit_price': float(product.unit_price),
                'stock_quantity': product.stock_quantity,
                'in_stock': product.in_stock,
                'minimum_order_quantity': product.minimum_order_quantity,
                'active': product.active,
                'brand': product.brand,
                'category': product.category,
                'size_variants': product.size_variants,
                'aliases': product.aliases,
                'keywords': product.keywords,
                'ai_training_examples': product.ai_training_examples,
                'common_misspellings': product.common_misspellings,
                'seasonal_patterns': product.seasonal_patterns
            })
        return catalog_dicts
    
    async def _handle_no_catalog_scenario(self, products: List[ExtractedProduct]) -> ValidationResult:
        """Handle case where no catalog is available."""
        logger.warning("No catalog available - all products require human validation")
        
        for product in products:
            product.status = "pending"
            product.validation_notes = "No catalog available - HUMAN VALIDATION REQUESTED"
        
        return ValidationResult(
            validated_products=products,
            requires_human_validation=True,
            human_validation_flags=[ValidationFlag.HUMAN_VALIDATION_REQUESTED, ValidationFlag.NO_CATALOG_MATCH],
            validation_summary="No product catalog available - all products require human validation",
            suggested_questions=["No tengo acceso al catálogo de productos. Un humano revisará tu pedido."],
            confidence_score=0.1
        )
    
    async def _handle_validation_error(self, products: List[ExtractedProduct], error: str) -> ValidationResult:
        """Handle validation errors gracefully."""
        logger.error(f"Validation error: {error}")
        
        for product in products:
            product.status = "pending"
            product.validation_notes = f"Validation error - HUMAN VALIDATION REQUESTED: {error}"
        
        return ValidationResult(
            validated_products=products,
            requires_human_validation=True,
            human_validation_flags=[ValidationFlag.HUMAN_VALIDATION_REQUESTED],
            validation_summary=f"Validation error occurred - human review required: {error}",
            suggested_questions=["Hubo un error técnico. Un humano revisará tu pedido."],
            confidence_score=0.0
        )
    
    async def _generate_validation_summary(
        self, issues: List[ProductValidationIssue], confidence: float
    ) -> str:
        """Generate human-readable validation summary."""
        if not issues:
            return f"All products validated successfully (confidence: {confidence:.0%})"
        
        issue_counts = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        summary_parts = [f"Validation completed with {confidence:.0%} confidence."]
        
        if issue_counts:
            issue_descriptions = []
            for issue_type, count in issue_counts.items():
                if count == 1:
                    issue_descriptions.append(f"1 product with {issue_type}")
                else:
                    issue_descriptions.append(f"{count} products with {issue_type}")
            
            summary_parts.append("Issues found: " + ", ".join(issue_descriptions))
        
        return " ".join(summary_parts)


# Factory function for easy integration
def create_enhanced_product_validator(
    database: DatabaseService, distributor_id: str
) -> EnhancedProductValidator:
    """Create enhanced product validator service."""
    return EnhancedProductValidator(database, distributor_id)