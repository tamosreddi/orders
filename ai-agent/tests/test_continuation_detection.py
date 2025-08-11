#!/usr/bin/env python3
"""
Test script for continuation detection functionality.

This script tests the multi-message order building feature with various scenarios.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to import our modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from services.continuation_detector import ContinuationDetector


def test_continuation_phrases():
    """Test basic continuation phrase detection."""
    detector = ContinuationDetector()
    
    test_cases = [
        # Explicit continuation phrases - should return high confidence
        ("también quiero 3 cocas", True, "explicit_continuation"),
        ("además necesito pan", True, "explicit_continuation"),
        ("y dame 2 leches", True, "explicit_continuation"),
        ("ah y ponme aceite", True, "explicit_continuation"),
        
        # Implicit continuation patterns - should return medium confidence
        ("y 3 cocas", True, "implicit_continuation"),
        ("ah aceite también", True, "implicit_continuation"),
        ("ponme leche", True, "implicit_continuation"),
        
        # Non-continuation phrases - should return False
        ("quiero 3 cocas", False, "new_order"),
        ("hola, ¿tienes pan?", False, "question"),
        ("gracias por todo", False, "gratitude"),
        ("buenos días", False, "greeting"),
    ]
    
    print("🔍 Testing Continuation Phrase Detection")
    print("=" * 50)
    
    for message, expected_continuation, test_type in test_cases:
        # Simulate having recent orders for testing
        mock_recent_orders = [{
            'id': 'order_123',
            'order_number': 'ORD-001',
            'status': 'PENDING',
            'created_at': '2025-08-07T10:00:00Z',
            'products': [
                {'product_name': 'leche', 'quantity': 2}
            ]
        }]
        
        result = detector._detect_continuation_rules(message, mock_recent_orders)
        
        status = "✅ PASS" if result.is_continuation == expected_continuation else "❌ FAIL"
        confidence_str = f"{result.confidence:.2f}"
        
        print(f"{status} | '{message}' → {result.is_continuation} (conf: {confidence_str}) | {test_type}")
        print(f"     Reasoning: {result.reasoning}")
        print(f"     Method: {result.detection_method}")
        print()

    print("\n" + "=" * 50)


def test_order_status_boundaries():
    """Test order status boundary logic."""
    detector = ContinuationDetector()
    
    print("🚧 Testing Order Status Boundaries")
    print("=" * 50)
    
    # Test cases for different order statuses
    test_scenarios = [
        # PENDING orders - should allow continuation
        ([{
            'id': 'order_123',
            'status': 'PENDING',
            'created_at': '2025-08-07T10:30:00Z'
        }], False, "PENDING order - can continue"),
        
        # ACCEPTED orders - should create new order
        ([{
            'id': 'order_123', 
            'status': 'ACCEPTED',
            'created_at': '2025-08-07T10:30:00Z'
        }], True, "ACCEPTED order - create new"),
        
        # REJECTED orders - should create new order
        ([{
            'id': 'order_123',
            'status': 'REJECTED', 
            'created_at': '2025-08-07T10:30:00Z'
        }], True, "REJECTED order - create new"),
        
        # No orders - should create new order
        ([], True, "No orders - create new"),
    ]
    
    for orders, should_create_new, scenario in test_scenarios:
        result = detector.should_create_new_order(orders)
        status = "✅ PASS" if result == should_create_new else "❌ FAIL"
        
        print(f"{status} | {scenario}: {result}")
    
    print("\n" + "=" * 50)


def test_time_boundaries():
    """Test time boundary logic for continuation."""
    from datetime import datetime, timedelta
    
    detector = ContinuationDetector()
    
    print("⏰ Testing Time Boundaries")
    print("=" * 50)
    
    now = datetime.now()
    
    test_scenarios = [
        # Recent order within window - should allow continuation
        ([{
            'id': 'order_123',
            'status': 'PENDING',
            'created_at': (now - timedelta(minutes=5)).isoformat()
        }], False, "Order 5 minutes ago - can continue"),
        
        # Old order outside window - should create new
        ([{
            'id': 'order_123',
            'status': 'PENDING', 
            'created_at': (now - timedelta(minutes=15)).isoformat()
        }], True, "Order 15 minutes ago - create new"),
        
        # Very recent order - should allow continuation
        ([{
            'id': 'order_123',
            'status': 'PENDING',
            'created_at': (now - timedelta(minutes=1)).isoformat()
        }], False, "Order 1 minute ago - can continue"),
    ]
    
    for orders, should_create_new, scenario in test_scenarios:
        result = detector.should_create_new_order(orders, time_threshold_minutes=10)
        status = "✅ PASS" if result == should_create_new else "❌ FAIL"
        
        print(f"{status} | {scenario}: {result}")
    
    print("\n" + "=" * 50)


def test_ai_context_generation():
    """Test AI context generation for continuation."""
    detector = ContinuationDetector()
    
    print("🤖 Testing AI Context Generation")
    print("=" * 50)
    
    # Test with multiple orders
    mock_orders = [
        {
            'id': 'order_123',
            'order_number': 'ORD-001',
            'status': 'PENDING',
            'products': [
                {'product_name': 'leche', 'quantity': 2},
                {'product_name': 'pan', 'quantity': 1},
                {'product_name': 'aceite', 'quantity': 1}
            ]
        },
        {
            'id': 'order_124',
            'order_number': 'ORD-002', 
            'status': 'ACCEPTED',
            'products': [
                {'product_name': 'coca cola', 'quantity': 6}
            ]
        }
    ]
    
    context = detector.get_continuation_context_for_ai(mock_orders)
    
    print("Generated AI Context:")
    print("-" * 30)
    print(context)
    print("-" * 30)
    
    # Check if context contains expected information
    expected_items = ['ORD-001', 'PENDING', 'leche', 'ORD-002', 'ACCEPTED']
    missing_items = []
    
    for item in expected_items:
        if item not in context:
            missing_items.append(item)
    
    if not missing_items:
        print("✅ PASS | Context contains all expected information")
    else:
        print(f"❌ FAIL | Missing items in context: {missing_items}")
    
    print("\n" + "=" * 50)


def main():
    """Run all continuation detection tests."""
    print("🚀 Starting Continuation Detection Tests")
    print("=" * 60)
    print()
    
    # Run test suites
    test_continuation_phrases()
    test_order_status_boundaries()
    test_time_boundaries()
    test_ai_context_generation()
    
    print("✨ Continuation Detection Tests Complete!")
    print("\nKey Features Tested:")
    print("- ✅ Explicit continuation phrase detection")
    print("- ✅ Implicit continuation pattern detection") 
    print("- ✅ Order status boundary logic (PENDING vs ACCEPTED/REJECTED)")
    print("- ✅ Time window boundaries for continuation")
    print("- ✅ AI context generation for recent orders")
    print("\nNext Steps:")
    print("1. Test with real OpenAI integration")
    print("2. Test with actual database connections")
    print("3. Test full end-to-end message processing")


if __name__ == "__main__":
    main()