// Direct Supabase API test for unit price update
// This tests the exact same call that our API should be making

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://ckapulfmocievprlnzux.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrYXB1bGZtb2NpZXZwcmxuenV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjE3Nzc4OTMsImV4cCI6MjAzNzM1Mzg5M30.bvzw6o6xSuCo8Pz9VglsWjBGjGRV6ZJ7QC3WUOCY5Xk' // This is the public anon key

const supabase = createClient(supabaseUrl, supabaseKey)

async function testDirectUnitPriceUpdate() {
  console.log('🧪 Testing direct Supabase unit price update...')
  
  const productId = '9a8ad83f-e240-4d97-8717-7876ac436e74'
  const distributorId = '550e8400-e29b-41d4-a716-446655440000'
  
  try {
    // Step 1: Set distributor context for RLS
    console.log('🔐 Setting distributor context...')
    const { error: contextError } = await supabase.rpc('set_distributor_context', { 
      distributor_uuid: distributorId 
    })
    
    if (contextError) {
      console.error('❌ Context error:', contextError)
      return false
    }
    
    // Step 2: Get current product data
    console.log('🔍 Fetching current product data...')
    const { data: currentProduct, error: fetchError } = await supabase
      .from('order_products')
      .select(`
        id,
        order_id,
        quantity,
        unit_price,
        line_price,
        orders!inner (
          distributor_id
        )
      `)
      .eq('id', productId)
      .single()
    
    if (fetchError) {
      console.error('❌ Fetch error:', fetchError)
      return false
    }
    
    console.log('📊 Current product data:', currentProduct)
    
    // Step 3: Calculate updates (simulating API logic)
    const updates = { unit_price: 9.50 } // Test price
    const newQuantity = updates.quantity !== undefined ? updates.quantity : currentProduct.quantity
    const newUnitPrice = updates.unit_price !== undefined ? updates.unit_price : currentProduct.unit_price  
    const calculatedLinePrice = newQuantity * newUnitPrice
    
    const finalUpdates = {
      ...updates,
      line_price: calculatedLinePrice,
      updated_at: new Date().toISOString()
    }
    
    console.log('📡 Sending update:', {
      productId,
      finalUpdates,
      calculation: {
        newQuantity,
        newUnitPrice,
        calculatedLinePrice
      }
    })
    
    // Step 4: Update the product
    const { data, error, count } = await supabase
      .from('order_products')
      .update(finalUpdates)
      .eq('id', productId)
      .select()
    
    if (error) {
      console.error('💥 Update error:', error)
      return false
    }
    
    console.log('✅ Update result:', { 
      data, 
      count, 
      recordsAffected: data ? data.length : 0 
    })
    
    // Step 5: Verify the result
    const { data: verifyData, error: verifyError } = await supabase
      .from('order_products')
      .select('id, product_name, quantity, unit_price, line_price, updated_at')
      .eq('id', productId)
      .single()
    
    if (verifyError) {
      console.error('❌ Verify error:', verifyError)
      return false
    }
    
    console.log('🔍 Verification result:', verifyData)
    
    return true
    
  } catch (error) {
    console.error('💥 Test failed:', error)
    return false
  }
}

// Run the test
testDirectUnitPriceUpdate().then(success => {
  if (success) {
    console.log('\n✅ DIRECT SUPABASE TEST: SUCCESS')
  } else {
    console.log('\n❌ DIRECT SUPABASE TEST: FAILED')  
  }
})