// Test script to verify unit price API updating
// Run this in the browser console on the Order Review page

async function testUnitPriceUpdate() {
  console.log('🧪 Testing unit price API update...');
  
  // Test data - updating the Aceite de Canola product
  const productId = '9a8ad83f-e240-4d97-8717-7876ac436e74';
  const newUnitPrice = 7.50; // Change from 6.00 to 7.50
  
  try {
    // Import the API function (this should work in Next.js environment)
    const { updateOrderProduct } = await import('/lib/api/orders.ts');
    
    console.log('📝 Calling updateOrderProduct with:', {
      productId,
      updates: { unit_price: newUnitPrice }
    });
    
    await updateOrderProduct(productId, {
      unit_price: newUnitPrice
    });
    
    console.log('✅ API call completed successfully!');
    console.log('🔍 Check the database to see if unit_price was updated to $7.50');
    
  } catch (error) {
    console.error('❌ API call failed:', error);
    console.error('Error details:', error.message);
  }
}

// Run the test
testUnitPriceUpdate();