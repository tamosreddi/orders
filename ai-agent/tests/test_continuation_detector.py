#!/usr/bin/env python3
"""
Test ContinuationDetector directly with simulated database responses.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.continuation_detector import ContinuationDetector
from services.database import DatabaseService


async def test_continuation_detector():
    """Test ContinuationDetector with mocked database responses."""
    
    print("🧪 CONTINUATION DETECTOR TEST")
    print("=" * 50)
    
    # Initialize components
    database = DatabaseService()
    detector = ContinuationDetector()
    
    test_distributor_id = "550e8400-e29b-41d4-a716-446655440000"
    test_customer_id = "customer-123"
    test_conversation_id = "conv-123"
    
    # Mock recent orders response
    mock_recent_orders = [{
        'id': 'order-123',
        'order_number': 'ORD-001',
        'status': 'PENDING',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'total_amount': 100.0,
        'customer_id': test_customer_id,
        'conversation_id': test_conversation_id
    }]
    
    # Test case 1: Temporal continuation scenario
    print("\n1️⃣ Testing temporal continuation ('2 pepsis' after recent order):")
    
    with patch.object(database, 'execute_query', new_callable=AsyncMock) as mock_db:
        # Mock database response for recent orders query
        mock_db.return_value = mock_recent_orders
        
        result = await detector.check_continuation(
            message_content="2 pepsis",
            conversation_id=test_conversation_id,
            customer_id=test_customer_id,
            database=database,
            distributor_id=test_distributor_id,
            extracted_products=[{"product_name": "pepsi", "quantity": 2}]
        )
        
        print(f"   Message: '2 pepsis'")
        print(f"   Is continuation: {result.is_continuation}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Target order: {result.target_order_id}")
        print(f"   Detection method: {result.detection_method}")
        print(f"   Reasoning: {result.reasoning}")
    
    # Test case 2: Explicit continuation phrase
    print("\n2️⃣ Testing explicit continuation ('también 3 cocas'):")
    
    with patch.object(database, 'execute_query', new_callable=AsyncMock) as mock_db:
        mock_db.return_value = mock_recent_orders
        
        result = await detector.check_continuation(
            message_content="también 3 cocas",
            conversation_id=test_conversation_id,
            customer_id=test_customer_id,
            database=database,
            distributor_id=test_distributor_id,
            extracted_products=[{"product_name": "coca", "quantity": 3}]
        )
        
        print(f"   Message: 'también 3 cocas'")
        print(f"   Is continuation: {result.is_continuation}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Target order: {result.target_order_id}")
        print(f"   Detection method: {result.detection_method}")
        print(f"   Reasoning: {result.reasoning}")
    
    # Test case 3: Non-continuation message  
    print("\n3️⃣ Testing non-continuation ('Hola'):")
    
    with patch.object(database, 'execute_query', new_callable=AsyncMock) as mock_db:
        mock_db.return_value = mock_recent_orders
        
        result = await detector.check_continuation(
            message_content="Hola",
            conversation_id=test_conversation_id,
            customer_id=test_customer_id,
            database=database,
            distributor_id=test_distributor_id,
            extracted_products=[]
        )
        
        print(f"   Message: 'Hola'")
        print(f"   Is continuation: {result.is_continuation}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Reasoning: {result.reasoning}")
    
    # Test case 4: No recent orders
    print("\n4️⃣ Testing with no recent orders:")
    
    with patch.object(database, 'execute_query', new_callable=AsyncMock) as mock_db:
        mock_db.return_value = []  # No recent orders
        
        result = await detector.check_continuation(
            message_content="2 pepsis",
            conversation_id=test_conversation_id,
            customer_id=test_customer_id,
            database=database,
            distributor_id=test_distributor_id,
            extracted_products=[{"product_name": "pepsi", "quantity": 2}]
        )
        
        print(f"   Message: '2 pepsis' (no recent orders)")
        print(f"   Is continuation: {result.is_continuation}")
        print(f"   Reasoning: {result.reasoning}")
    
    print("\n" + "=" * 50)
    print("✅ CONTINUATION DETECTOR TEST COMPLETED")


if __name__ == "__main__":
    asyncio.run(test_continuation_detector())