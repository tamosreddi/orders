#!/usr/bin/env python3
"""
Simulate the exact unit price update flow that happens in the frontend.
This will help us identify where the issue is.
"""

import asyncio
import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def simulate_unit_price_update():
    """Simulate the exact unit price update that should happen from frontend."""
    
    logger.info("🧪 Simulating unit price update from $6.00 to $8.00")
    
    try:
        # Import the actual API function
        import sys
        sys.path.append('/Users/macbook/orderagent')
        
        from lib.api.orders import updateOrderProduct
        
        # Test data - exact same as what frontend should send
        product_id = "9a8ad83f-e240-4d97-8717-7876ac436e74"
        updates = {
            "unit_price": 8.00  # This is what frontend sends for unitPrice field
        }
        
        logger.info(f"📝 Calling updateOrderProduct with:")
        logger.info(f"  Product ID: {product_id}")
        logger.info(f"  Updates: {updates}")
        
        # This should call the same API function the frontend calls
        await updateOrderProduct(product_id, updates)
        
        logger.info("✅ API call completed!")
        logger.info("🔍 Check database to verify unit_price updated to $8.00")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the simulation."""
    success = await simulate_unit_price_update()
    
    if success:
        print("\n✅ UNIT PRICE SIMULATION: SUCCESS")
    else:
        print("\n❌ UNIT PRICE SIMULATION: FAILED")

if __name__ == "__main__":
    asyncio.run(main())