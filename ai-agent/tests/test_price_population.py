#!/usr/bin/env python3
"""
Test script for catalog price auto-population.

Tests the end-to-end flow:
1. Create test order with matched products
2. Verify prices are auto-populated from catalog
3. Verify line_price calculations are correct
"""

import asyncio
import logging
import uuid
from decimal import Decimal
from datetime import datetime

from services.database import DatabaseService
from schemas.order import OrderCreation, OrderProduct
from tools.supabase_tools import create_order

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_catalog_price_population():
    """Test that catalog prices are automatically populated for matched products."""
    
    logger.info("🧪 Starting catalog price population test")
    
    try:
        # Initialize database connection
        db = DatabaseService()
        
        # Test distributor ID
        distributor_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create test order with matched products (but no prices)
        test_products = [
            OrderProduct(
                product_name="Aceite de Canola 1L",
                quantity=2,
                unit="litros",
                unit_price=None,  # Should be auto-populated to $5.75
                line_price=None,  # Should be auto-calculated to $11.50
                ai_confidence=0.95,
                original_text="2 litros de aceite de canola",
                matched_product_id="229578f5-8d68-4cae-9e4c-4e96f82f2e3e",  # Aceite de Canola 1L
                matching_confidence=0.95
            ),
            OrderProduct(
                product_name="Aceite de Oliva Extra Virgen 500ml",
                quantity=1,
                unit="botella",
                unit_price=None,  # Should be auto-populated to $12.25
                line_price=None,  # Should be auto-calculated to $12.25
                ai_confidence=0.90,
                original_text="una botella de aceite de oliva",
                matched_product_id="8a47bf36-04b0-4490-8956-7ef7303a57e8",  # Aceite de Oliva
                matching_confidence=0.90
            )
        ]
        
        # Use existing IDs for test
        test_customer_id = "cadf2c84-8b54-4062-88e5-55b646116018"
        test_conversation_id = "56d78925-2a57-4ff8-93dd-27e5557d0d8c"
        test_message_id = "17e92bbf-98de-4803-9fa9-568b1b2185bc"
        
        order_data = OrderCreation(
            customer_id=test_customer_id,
            distributor_id=distributor_id,
            conversation_id=test_conversation_id,
            channel="WHATSAPP",
            products=test_products,
            additional_comment="Test order for price population",
            ai_confidence=0.92,
            source_message_ids=[test_message_id]
        )
        
        logger.info(f"📝 Creating test order with {len(test_products)} products")
        logger.info("Products before price population:")
        for i, product in enumerate(test_products):
            logger.info(f"  {i+1}. {product.product_name}: unit_price={product.unit_price}, line_price={product.line_price}")
        
        # Create the order (this should trigger catalog price population)
        order_id = await create_order(db, order_data)
        
        if not order_id:
            logger.error("❌ Failed to create test order")
            return False
        
        logger.info(f"✅ Created test order: {order_id}")
        
        # Verify that prices were populated correctly in database
        
        order_products = await db.execute_query(
            table='order_products',
            operation='select',
            filters={'order_id': order_id},
            distributor_id=None
        )
        
        if not order_products:
            logger.error("❌ No order products found in database")
            return False
        
        logger.info("🔍 Verifying populated prices:")
        
        expected_prices = {
            "229578f5-8d68-4cae-9e4c-4e96f82f2e3e": {"unit_price": 5.75, "quantity": 2, "line_price": 11.50},
            "8a47bf36-04b0-4490-8956-7ef7303a57e8": {"unit_price": 12.25, "quantity": 1, "line_price": 12.25}
        }
        
        success = True
        total_expected = Decimal('0')
        
        for product in order_products:
            matched_id = product['matched_product_id']
            actual_unit_price = float(product['unit_price'])
            actual_line_price = float(product['line_price'])
            actual_quantity = product['quantity']
            
            if matched_id in expected_prices:
                expected = expected_prices[matched_id]
                
                # Check unit price
                if abs(actual_unit_price - expected['unit_price']) < 0.01:
                    logger.info(f"  ✅ {product['product_name']}: unit_price=${actual_unit_price} (correct)")
                else:
                    logger.error(f"  ❌ {product['product_name']}: unit_price=${actual_unit_price}, expected=${expected['unit_price']}")
                    success = False
                
                # Check line price
                if abs(actual_line_price - expected['line_price']) < 0.01:
                    logger.info(f"  ✅ {product['product_name']}: line_price=${actual_line_price} (correct)")
                else:
                    logger.error(f"  ❌ {product['product_name']}: line_price=${actual_line_price}, expected=${expected['line_price']}")
                    success = False
                
                # Check quantity
                if actual_quantity == expected['quantity']:
                    logger.info(f"  ✅ {product['product_name']}: quantity={actual_quantity} (correct)")
                else:
                    logger.error(f"  ❌ {product['product_name']}: quantity={actual_quantity}, expected={expected['quantity']}")
                    success = False
                
                total_expected += Decimal(str(expected['line_price']))
            else:
                logger.warning(f"  ⚠️ Unknown matched_product_id: {matched_id}")
        
        # Check order total
        order_info = await db.execute_query(
            table='orders',
            operation='select',
            filters={'id': order_id},
            distributor_id=distributor_id
        )
        
        if order_info:
            actual_total = float(order_info[0]['total_amount'])
            expected_total = float(total_expected)
            
            if abs(actual_total - expected_total) < 0.01:
                logger.info(f"✅ Order total: ${actual_total} (correct)")
            else:
                logger.error(f"❌ Order total: ${actual_total}, expected=${expected_total}")
                success = False
        
        if success:
            logger.info("🎉 All catalog price population tests PASSED!")
            return True
        else:
            logger.error("💥 Some catalog price population tests FAILED!")
            return False
        
    except Exception as e:
        logger.error(f"💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the catalog price population test."""
    success = await test_catalog_price_population()
    
    if success:
        print("\n🎉 CATALOG PRICE POPULATION TEST: PASSED")
        exit(0)
    else:
        print("\n💥 CATALOG PRICE POPULATION TEST: FAILED")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())