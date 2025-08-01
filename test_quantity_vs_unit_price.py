#!/usr/bin/env python3
"""
Compare quantity vs unit_price editing to identify the difference.
This will help us understand why quantity works but unit_price doesn't.
"""

import asyncio
import json
import logging
from decimal import Decimal

# Configure logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quantity_update():
    """Test quantity update (which supposedly works)."""
    
    logger.info("🔢 Testing QUANTITY update (should work)")
    
    try:
        # Test data
        product_id = '9a8ad83f-e240-4d97-8717-7876ac436e74'
        
        # Reset to known state first
        import subprocess
        
        # Simulate quantity change from 2 to 3
        updates = {"quantity": 3}
        
        logger.info(f"📝 Quantity update test:")
        logger.info(f"  Product ID: {product_id}")  
        logger.info(f"  Updates: {updates}")
        logger.info(f"  Expected: quantity=3, line_price=3*8.00=24.00")
        
        # This would be the API call: await updateOrderProduct(product_id, updates)
        # For now, let's simulate it with direct SQL
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Quantity test failed: {e}")
        return False

async def test_unit_price_update():
    """Test unit_price update (which supposedly doesn't work)."""
    
    logger.info("💲 Testing UNIT_PRICE update (reportedly broken)")
    
    try:
        # Test data
        product_id = '9a8ad83f-e240-4d97-8717-7876ac436e74'
        
        # Simulate unit_price change from 8.00 to 10.00
        updates = {"unit_price": 10.00}
        
        logger.info(f"📝 Unit price update test:")
        logger.info(f"  Product ID: {product_id}")
        logger.info(f"  Updates: {updates}")
        logger.info(f"  Expected: unit_price=10.00, line_price=2*10.00=20.00")
        
        # This would be the API call: await updateOrderProduct(product_id, updates)
        # For now, let's simulate it with direct SQL
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Unit price test failed: {e}")
        return False

async def compare_frontend_data_flow():
    """Compare the data flow for both types of updates."""
    
    logger.info("🔍 Comparing frontend data flow...")
    
    # Simulate frontend EditableProductsTable logic
    
    # QUANTITY UPDATE SCENARIO
    logger.info("\n📊 QUANTITY UPDATE SCENARIO:")
    
    # Initial product state
    product = {
        "id": "9a8ad83f-e240-4d97-8717-7876ac436e74",
        "name": "Aceite de Canola 1L", 
        "quantity": 2,
        "unitPrice": 8.00,
        "linePrice": 16.00
    }
    
    # User edits quantity from 2 to 3
    field = 'quantity'
    value = '3'  # Frontend sends as string
    
    # Frontend logic (lines 31-41 in EditableProductsTable.tsx)
    if field == 'quantity' or field == 'unitPrice':
        numValue = float(value) if isinstance(value, str) else value
        updatedProduct = {
            **product,
            field: numValue,  # quantity: 3
            "linePrice": numValue * product["unitPrice"] if field == 'quantity' else product["quantity"] * numValue  # 3 * 8.00 = 24.00
        }
        updatedProduct[field] = numValue
        if field == 'quantity':
            updatedProduct["linePrice"] = numValue * product["unitPrice"]  # 3 * 8.00 = 24.00
        elif field == 'unitPrice':
            updatedProduct["linePrice"] = product["quantity"] * numValue  # 2 * numValue
    
    # API mapping (lines 59-60)
    updates = {}
    if field == 'quantity':
        updates["quantity"] = updatedProduct["quantity"]  # 3
    if field == 'unitPrice':
        updates["unit_price"] = updatedProduct["unitPrice"]  # Should be new price
    
    logger.info(f"  Frontend product state: {updatedProduct}")
    logger.info(f"  API updates sent: {updates}")
    
    # UNIT PRICE UPDATE SCENARIO
    logger.info("\n💰 UNIT PRICE UPDATE SCENARIO:")
    
    # Reset product state
    product = {
        "id": "9a8ad83f-e240-4d97-8717-7876ac436e74",
        "name": "Aceite de Canola 1L",
        "quantity": 2, 
        "unitPrice": 8.00,
        "linePrice": 16.00
    }
    
    # User edits unit price from 8.00 to 10.00
    field = 'unitPrice'
    value = '10.00'  # Frontend sends as string
    
    # Frontend logic
    if field == 'quantity' or field == 'unitPrice':
        numValue = float(value)  # 10.00
        updatedProduct = {
            **product,
            field: numValue,  # unitPrice: 10.00
            "linePrice": product["quantity"] * numValue if field == 'unitPrice' else numValue * product["unitPrice"]  # 2 * 10.00 = 20.00
        }
        updatedProduct[field] = numValue
        if field == 'quantity':
            updatedProduct["linePrice"] = numValue * product["unitPrice"]
        elif field == 'unitPrice':
            updatedProduct["linePrice"] = product["quantity"] * numValue  # 2 * 10.00 = 20.00
    
    # API mapping
    updates = {}
    if field == 'quantity':
        updates["quantity"] = updatedProduct["quantity"]
    if field == 'unitPrice':
        updates["unit_price"] = updatedProduct["unitPrice"]  # 10.00
        
    logger.info(f"  Frontend product state: {updatedProduct}")
    logger.info(f"  API updates sent: {updates}")
    
    logger.info("\n🔍 COMPARISON RESULTS:")
    logger.info("  Both scenarios follow the same logic pattern")
    logger.info("  Both should send correct data to the API")
    logger.info("  The issue must be in the API layer or RLS policies")

async def main():
    """Run the comparison tests."""
    
    await compare_frontend_data_flow()
    
    logger.info("\n🎯 NEXT STEPS:")
    logger.info("  1. Check if the issue is in the browser console logs")
    logger.info("  2. Verify that unit_price updates reach the API function")
    logger.info("  3. Check if there's a type conversion issue in the API")
    logger.info("  4. Test with real frontend in browser developer tools")

if __name__ == "__main__":
    asyncio.run(main())