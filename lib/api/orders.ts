import { supabase } from '../supabase/client';
import type { Database } from '../supabase/types';
import { Order, OrderDetails, OrderProduct } from '../../types/order';

/**
 * User-friendly error messages for order operations
 */
export const ORDER_ERROR_MESSAGES = {
  NETWORK_ERROR: 'Connection failed. Please check your internet and try again',
  VALIDATION_ERROR: 'Please check the highlighted fields',
  UNKNOWN_ERROR: 'Something went wrong. Please try again',
  PERMISSION_DENIED: 'You do not have permission to perform this action',
  ORDER_NOT_FOUND: 'Order not found',
  CUSTOMER_NOT_FOUND: 'Customer not found for this order',
  UPDATE_FAILED: 'Failed to update order status'
} as const;

/**
 * Custom error class for order operations
 */
export class OrderError extends Error {
  constructor(
    message: string,
    public code: keyof typeof ORDER_ERROR_MESSAGES,
    public originalError?: any
  ) {
    super(message);
    this.name = 'OrderError';
  }
}

/**
 * Converts Supabase errors to user-friendly OrderError
 */
function handleSupabaseError(error: any): OrderError {
  // Handle specific Supabase error codes
  if (error.code === 'PGRST301') { // Permission denied
    return new OrderError(ORDER_ERROR_MESSAGES.PERMISSION_DENIED, 'PERMISSION_DENIED', error);
  }
  
  if (error.code === 'PGRST116') { // Not found
    return new OrderError(ORDER_ERROR_MESSAGES.ORDER_NOT_FOUND, 'ORDER_NOT_FOUND', error);
  }
  
  // Network or unknown errors
  return new OrderError(ORDER_ERROR_MESSAGES.UNKNOWN_ERROR, 'UNKNOWN_ERROR', error);
}

// Database types
type OrderRow = {
  id: string;
  customer_id: string;
  conversation_id: string | null;
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  status: 'CONFIRMED' | 'PENDING' | 'REVIEW';
  received_date: string;
  received_time: string;
  delivery_date: string | null;
  postal_code: string | null;
  delivery_address: string | null;
  total_amount: number;
  additional_comment: string | null;
  whatsapp_message: string | null;
  ai_generated: boolean | null;
  ai_confidence: number | null;
  ai_source_message_id: string | null;
  requires_review: boolean | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  external_order_id: string | null;
  created_at: string;
  updated_at: string;
  distributor_id: string;
  data_expired: boolean | null;
};

type OrderProductRow = {
  id: string;
  order_id: string;
  product_name: string;
  product_unit: string;
  quantity: number;
  unit_price: number;
  line_price: number;
  ai_extracted: boolean | null;
  ai_confidence: number | null;
  ai_original_text: string | null;
  suggested_product_id: string | null;
  manual_override: boolean | null;
  line_order: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  matched_product_id: string | null;
  matching_confidence: number | null;
  matching_method: string | null;
  matching_score: number | null;
  alternative_matches: any;
};

type CustomerRow = {
  id: string;
  business_name: string;
  customer_code: string;
  avatar_url: string | null;
};

/**
 * Development distributor configuration for testing
 */
interface DevDistributor {
  id: string;
  name: string;
  email: string;
}

const DEV_DISTRIBUTORS: DevDistributor[] = [
  { id: '550e8400-e29b-41d4-a716-446655440000', name: 'Acme Foods Distribution', email: 'admin@acmefoods.com' },
  { id: '550e8400-e29b-41d4-a716-446655440001', name: 'Beta Beverages Co.', email: 'owner@betabev.com' }
];

/**
 * Gets the current user's distributor ID from the session
 * For development, we use a placeholder distributor until authentication is implemented
 */
function getCurrentDistributorId(): string {
  // TODO: This should come from useAuth() hook when called from React components
  // For now, return the first development distributor ID for testing
  const currentDistributor = DEV_DISTRIBUTORS[0];
  
  console.log(`🧪 Development Mode: Using distributor "${currentDistributor.name}" (${currentDistributor.id})`);
  
  return currentDistributor.id;
}

/**
 * Converts Supabase order data to frontend Order type
 */
function mapSupabaseOrderToFrontend(
  orderRow: OrderRow,
  customerRow: CustomerRow,
  productCount: number
): Order {
  // Format received time from database time to display format
  const formatTime = (timeString: string): string => {
    const [hours, minutes] = timeString.split(':');
    const hour24 = parseInt(hours);
    const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
    const period = hour24 >= 12 ? 'PM' : 'AM';
    return `${hour12}:${minutes} ${period}`;
  };

  return {
    id: orderRow.id,
    customer: {
      name: customerRow.business_name,
      avatar: customerRow.avatar_url || '/logos/default-avatar.png',
      code: customerRow.customer_code,
    },
    channel: orderRow.channel,
    receivedDate: orderRow.received_date,
    receivedTime: formatTime(orderRow.received_time),
    deliveryDate: orderRow.delivery_date || 'por confirmar',
    products: productCount,
    status: orderRow.status === 'CONFIRMED' ? 'CONFIRMED' : 
            orderRow.status === 'REVIEW' ? 'REVIEW' : 'PENDING'
  };
}

/**
 * Gets all orders for the current distributor with customer data and product counts
 */
export async function getOrders(): Promise<Order[]> {
  try {
    const distributorId = getCurrentDistributorId();

    // Get orders with customer data using a join
    const { data: ordersWithCustomers, error: ordersError } = await supabase
      .from('orders')
      .select(`
        *,
        customers!inner (
          id,
          business_name,
          customer_code,
          avatar_url
        )
      `)
      .eq('distributor_id', distributorId)
      .order('created_at', { ascending: false });

    if (ordersError) {
      throw handleSupabaseError(ordersError);
    }

    if (!ordersWithCustomers || ordersWithCustomers.length === 0) {
      return [];
    }

    // Get product counts for all orders in one query
    const orderIds = ordersWithCustomers.map(o => o.id);
    const { data: productCounts, error: productCountError } = await supabase
      .from('order_products')
      .select('order_id')
      .in('order_id', orderIds);

    if (productCountError) {
      console.warn('Failed to fetch product counts:', productCountError.message);
    }

    // Count products by order_id
    const productCountMap: Record<string, number> = {};
    productCounts?.forEach(pc => {
      productCountMap[pc.order_id] = (productCountMap[pc.order_id] || 0) + 1;
    });

    // Map to frontend format
    return ordersWithCustomers.map(orderData => {
      const customer = Array.isArray(orderData.customers) 
        ? orderData.customers[0] 
        : orderData.customers;
      
      return mapSupabaseOrderToFrontend(
        orderData as OrderRow,
        customer as CustomerRow,
        productCountMap[orderData.id] || 0
      );
    });

  } catch (error) {
    console.error('Error fetching orders:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Gets a single order by ID with detailed information
 */
export async function getOrderById(orderId: string): Promise<OrderDetails | null> {
  try {
    const distributorId = getCurrentDistributorId();

    // Get order with customer data and original message
    const { data: orderData, error: orderError } = await supabase
      .from('orders')
      .select(`
        *,
        customers!inner (
          id,
          business_name,
          customer_code,
          avatar_url,
          address
        ),
        original_message:messages!ai_source_message_id (
          id,
          content,
          created_at
        )
      `)
      .eq('id', orderId)
      .eq('distributor_id', distributorId)
      .single();

    if (orderError) {
      if (orderError.code === 'PGRST116') {
        return null; // Order not found
      }
      throw handleSupabaseError(orderError);
    }

    // Get order products
    const { data: orderProducts, error: productsError } = await supabase
      .from('order_products')
      .select('*')
      .eq('order_id', orderId)
      .order('line_order', { ascending: true });

    if (productsError) {
      throw handleSupabaseError(productsError);
    }

    const customer = Array.isArray(orderData.customers) 
      ? orderData.customers[0] 
      : orderData.customers;
    
    const originalMessage = orderData.original_message;

    // Format time for display
    const formatTime = (timeString: string): string => {
      if (!timeString) return '';
      const [hours, minutes] = timeString.split(':');
      const hour24 = parseInt(hours);
      const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
      const period = hour24 >= 12 ? 'PM' : 'AM';
      return `${hour12}:${minutes} ${period}`;
    };

    // Map order products to frontend format
    const products: OrderProduct[] = orderProducts?.map(p => ({
      id: p.id,
      name: p.product_name,
      unit: p.product_unit,
      quantity: p.quantity,
      unitPrice: p.unit_price,
      linePrice: p.line_price
    })) || [];

    const orderDetails: OrderDetails = {
      id: orderData.id,
      customer: {
        name: customer.business_name,
        avatar: customer.avatar_url || '/logos/default-avatar.png',
        code: customer.customer_code,
        address: customer.address || 'No address available'
      },
      channel: orderData.channel,
      receivedDate: orderData.received_date,
      receivedTime: formatTime(orderData.received_time),
      deliveryDate: orderData.delivery_date || 'por confirmar',
      postalCode: orderData.postal_code || '',
      products: products,
      totalAmount: orderData.total_amount,
      additionalComment: orderData.additional_comment || '',
      attachments: [], // TODO: Implement attachments from order_attachments table
      whatsappMessage: orderData.whatsapp_message || '',
      originalMessage: originalMessage ? {
        id: originalMessage.id,
        content: originalMessage.content,
        timestamp: originalMessage.created_at
      } : null,
      status: orderData.status === 'CONFIRMED' ? 'CONFIRMED' : 
              orderData.status === 'REVIEW' ? 'REVIEW' : 'PENDING'
    };

    return orderDetails;

  } catch (error) {
    console.error('Error fetching order by ID:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Updates an order's status
 */
export async function updateOrderStatus(orderId: string, status: Order['status']): Promise<void> {
  try {
    const distributorId = getCurrentDistributorId();

    const { error } = await supabase
      .from('orders')
      .update({ 
        status: status,
        updated_at: new Date().toISOString()
      })
      .eq('id', orderId)
      .eq('distributor_id', distributorId);

    if (error) {
      throw handleSupabaseError(error);
    }

  } catch (error) {
    console.error('Error updating order status:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Updates multiple orders' status in bulk
 */
export async function bulkUpdateOrderStatus(orderIds: string[], status: Order['status']): Promise<void> {
  try {
    const distributorId = getCurrentDistributorId();

    const { error } = await supabase
      .from('orders')
      .update({ 
        status: status,
        updated_at: new Date().toISOString()
      })
      .in('id', orderIds)
      .eq('distributor_id', distributorId);

    if (error) {
      throw handleSupabaseError(error);
    }

  } catch (error) {
    console.error('Error bulk updating order status:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Updates a single order product
 */
export async function updateOrderProduct(
  orderProductId: string, 
  updates: Partial<{
    product_name: string;
    product_unit: string;
    quantity: number;
    unit_price: number;
    line_price: number;
  }>
): Promise<void> {
  try {
    const distributorId = getCurrentDistributorId();
    
    // Enhanced debugging for unit_price issues
    console.log('🐛 DEBUG: updateOrderProduct called with:', {
      orderProductId,
      updates,
      updateKeys: Object.keys(updates),
      hasUnitPrice: 'unit_price' in updates,
      unitPriceValue: updates.unit_price,
      unitPriceType: typeof updates.unit_price
    });
    
    // Set distributor context for RLS
    await supabase.rpc('set_distributor_context', { distributor_uuid: distributorId });
    console.log('🔐 Set distributor context:', distributorId);

    // Get current product data to calculate proper line_price
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
      .eq('id', orderProductId)
      .single();

    console.log('🔍 Current product data:', {
      orderProductId,
      distributorId,
      currentProduct,
      fetchError
    });

    if (fetchError) {
      console.error('❌ Fetch error:', fetchError);
      throw handleSupabaseError(fetchError);
    }

    if (!currentProduct) {
      console.error('❌ No order product found for ID:', orderProductId);
      throw new OrderError(ORDER_ERROR_MESSAGES.ORDER_NOT_FOUND, 'ORDER_NOT_FOUND');
    }

    if (currentProduct.orders.distributor_id !== distributorId) {
      console.error('❌ Permission denied - distributor mismatch:', {
        expected: distributorId,
        actual: currentProduct.orders.distributor_id
      });
      throw new OrderError(ORDER_ERROR_MESSAGES.PERMISSION_DENIED, 'PERMISSION_DENIED');
    }

    console.log('✅ Security check passed');

    // Calculate the correct line_price based on current and updated values
    const newQuantity = updates.quantity !== undefined ? updates.quantity : currentProduct.quantity;
    const newUnitPrice = updates.unit_price !== undefined ? updates.unit_price : currentProduct.unit_price;
    const calculatedLinePrice = newQuantity * newUnitPrice;

    // Prepare the final updates with calculated line_price
    const finalUpdates = {
      ...updates,
      line_price: calculatedLinePrice, // Always recalculate line_price
      updated_at: new Date().toISOString()
    };

    console.log('📡 Supabase update:', {
      table: 'order_products',
      id: orderProductId,
      originalUpdates: updates,
      finalUpdates: finalUpdates,
      calculation: {
        newQuantity,
        newUnitPrice,
        calculatedLinePrice
      }
    });

    // Enhanced debugging: Log the exact Supabase call
    console.log('🔍 About to call Supabase with:', {
      table: 'order_products',
      updateData: finalUpdates,
      whereClause: `id = ${orderProductId}`,
      expectingSelect: true
    });

    const { data, error, count } = await supabase
      .from('order_products')
      .update(finalUpdates)
      .eq('id', orderProductId)
      .select();
      
    // Enhanced debugging: Log detailed results
    console.log('📊 Detailed Supabase result:', {
      success: !error,
      error: error,
      data: data,
      count: count,
      recordsAffected: data ? data.length : 0,
      updatedRecord: data && data.length > 0 ? data[0] : null
    });

    if (error) {
      console.error('💥 Supabase error:', error);
      throw handleSupabaseError(error);
    }

    console.log('✅ Supabase update result:', { 
      data, 
      count, 
      recordsAffected: data ? data.length : 0 
    });

    // Update the order's total amount if prices changed
    if (updates.unit_price !== undefined || updates.quantity !== undefined || updates.line_price !== undefined) {
      await updateOrderTotal(currentProduct.order_id);
    }

  } catch (error) {
    console.error('Error updating order product:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Adds a new product to an order
 */
export async function addOrderProduct(
  orderId: string,
  productData: {
    product_name: string;
    product_unit: string;
    quantity: number;
    unit_price: number;
    line_price: number;
  }
): Promise<OrderProduct> {
  try {
    const distributorId = getCurrentDistributorId();

    // Verify the order belongs to the current distributor
    const { data: order, error: orderError } = await supabase
      .from('orders')
      .select('id, distributor_id')
      .eq('id', orderId)
      .eq('distributor_id', distributorId)
      .single();

    if (orderError || !order) {
      throw new OrderError(ORDER_ERROR_MESSAGES.ORDER_NOT_FOUND, 'ORDER_NOT_FOUND');
    }

    // Get the next line_order number
    const { data: maxLineOrder } = await supabase
      .from('order_products')
      .select('line_order')
      .eq('order_id', orderId)
      .order('line_order', { ascending: false })
      .limit(1)
      .single();

    const nextLineOrder = (maxLineOrder?.line_order || 0) + 1;

    // Insert the new product
    const { data: newProduct, error: insertError } = await supabase
      .from('order_products')
      .insert([{
        order_id: orderId,
        product_name: productData.product_name,
        product_unit: productData.product_unit,
        quantity: productData.quantity,
        unit_price: productData.unit_price,
        line_price: productData.line_price,
        line_order: nextLineOrder,
        ai_extracted: false,
        manual_override: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }])
      .select()
      .single();

    if (insertError) {
      throw handleSupabaseError(insertError);
    }

    // Update the order's total amount
    await updateOrderTotal(orderId);

    // Return the new product in frontend format
    return {
      id: newProduct.id,
      name: newProduct.product_name,
      unit: newProduct.product_unit,
      quantity: newProduct.quantity,
      unitPrice: newProduct.unit_price,
      linePrice: newProduct.line_price
    };

  } catch (error) {
    console.error('Error adding order product:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Deletes a product from an order
 */
export async function deleteOrderProduct(orderProductId: string): Promise<void> {
  try {
    const distributorId = getCurrentDistributorId();

    // Verify the order product belongs to the current distributor and get order_id
    const { data: orderProduct, error: fetchError } = await supabase
      .from('order_products')
      .select(`
        id,
        order_id,
        orders!inner (
          distributor_id
        )
      `)
      .eq('id', orderProductId)
      .single();

    if (fetchError) {
      throw handleSupabaseError(fetchError);
    }

    if (!orderProduct || orderProduct.orders.distributor_id !== distributorId) {
      throw new OrderError(ORDER_ERROR_MESSAGES.PERMISSION_DENIED, 'PERMISSION_DENIED');
    }

    // Delete the order product
    const { error } = await supabase
      .from('order_products')
      .delete()
      .eq('id', orderProductId);

    if (error) {
      throw handleSupabaseError(error);
    }

    // Update the order's total amount
    await updateOrderTotal(orderProduct.order_id);

  } catch (error) {
    console.error('Error deleting order product:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Updates an order's delivery date
 */
export async function updateOrderDeliveryDate(orderId: string, deliveryDate: string): Promise<void> {
  try {
    const distributorId = getCurrentDistributorId();

    const { error } = await supabase
      .from('orders')
      .update({ 
        delivery_date: deliveryDate,
        updated_at: new Date().toISOString()
      })
      .eq('id', orderId)
      .eq('distributor_id', distributorId);

    if (error) {
      throw handleSupabaseError(error);
    }

  } catch (error) {
    console.error('Error updating order delivery date:', error);
    if (error instanceof OrderError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Helper function to recalculate and update order total
 */
async function updateOrderTotal(orderId: string): Promise<void> {
  try {
    // Get all products for this order
    const { data: products, error: productsError } = await supabase
      .from('order_products')
      .select('line_price')
      .eq('order_id', orderId);

    if (productsError) {
      throw handleSupabaseError(productsError);
    }

    // Calculate new total
    const newTotal = products?.reduce((sum, product) => sum + (product.line_price || 0), 0) || 0;

    // Update the order total
    const { error: updateError } = await supabase
      .from('orders')
      .update({ 
        total_amount: newTotal,
        updated_at: new Date().toISOString()
      })
      .eq('id', orderId);

    if (updateError) {
      throw handleSupabaseError(updateError);
    }

  } catch (error) {
    console.warn('Failed to update order total:', error);
  }
}