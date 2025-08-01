'use client';

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../../../lib/supabase/client';
import { Order } from '../../../types/order';
import { getOrders, updateOrderStatus, bulkUpdateOrderStatus, OrderError } from '../../../lib/api/orders';

/**
 * Gets the current distributor ID for the session
 * TODO: This should come from useAuth() hook when authentication is implemented
 */
function getCurrentDistributorId(): string {
  // Use the same development distributor ID from lib/api/orders.ts
  const DEV_DISTRIBUTOR_ID = '550e8400-e29b-41d4-a716-446655440000';
  return DEV_DISTRIBUTOR_ID;
}

interface UseOrdersOptions {
  distributorId: string;
}

interface UseOrdersReturn {
  // Orders
  orders: Order[];
  ordersLoading: boolean;
  ordersError: string | null;
  
  // Actions
  updateStatus: (orderId: string, status: Order['status']) => Promise<void>;
  bulkUpdateStatus: (orderIds: string[], status: Order['status']) => Promise<void>;
  
  // Real-time
  refreshOrders: () => Promise<void>;
}

export function useOrders({ distributorId }: UseOrdersOptions): UseOrdersReturn {
  // Orders state
  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState<string | null>(null);

  // Load orders with error handling
  const loadOrders = useCallback(async (isInitialLoad: boolean = false) => {
    try {
      if (isInitialLoad) {
        console.log('loadOrders: Initial load...');
        setOrdersLoading(true);
      }
      setOrdersError(null);

      const ordersData = await getOrders();
      
      // Only update state if data has actually changed
      setOrders(prev => {
        const hasChanged = JSON.stringify(prev) !== JSON.stringify(ordersData);
        if (hasChanged || isInitialLoad) {
          console.log('loadOrders: Data changed, updating state');
          return ordersData;
        }
        return prev;
      });
    } catch (error) {
      console.error('Error loading orders:', error);
      if (error instanceof OrderError) {
        setOrdersError(error.message);
      } else {
        setOrdersError('Failed to load orders. Please try again.');
      }
    } finally {
      if (isInitialLoad) {
        setOrdersLoading(false);
      }
    }
  }, []);

  // Update single order status
  const updateStatus = useCallback(async (orderId: string, status: Order['status']) => {
    try {
      await updateOrderStatus(orderId, status);
      
      // Optimistically update local state
      setOrders(prev => 
        prev.map(order => 
          order.id === orderId 
            ? { ...order, status }
            : order
        )
      );
      
      // Refresh from server to ensure consistency
      await loadOrders();
    } catch (error) {
      console.error('Error updating order status:', error);
      // Revert optimistic update by refreshing from server
      await loadOrders();
      throw error;
    }
  }, [loadOrders]);

  // Update multiple orders status
  const bulkUpdateStatus = useCallback(async (orderIds: string[], status: Order['status']) => {
    try {
      await bulkUpdateOrderStatus(orderIds, status);
      
      // Optimistically update local state
      setOrders(prev => 
        prev.map(order => 
          orderIds.includes(order.id) 
            ? { ...order, status }
            : order
        )
      );
      
      // Refresh from server to ensure consistency
      await loadOrders();
    } catch (error) {
      console.error('Error bulk updating order status:', error);
      // Revert optimistic update by refreshing from server
      await loadOrders();
      throw error;
    }
  }, [loadOrders]);

  // Load orders on mount
  useEffect(() => {
    loadOrders(true); // Initial load
  }, [loadOrders]);

  // Set up real-time subscriptions for live updates
  useEffect(() => {
    console.log('Setting up real-time subscriptions for orders...');
    console.log('Distributor ID:', distributorId);
    
    // Set up orders subscription
    const ordersChannel = supabase.channel(`orders_changes_${Date.now()}`);
    
    ordersChannel
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'orders',
          filter: `distributor_id=eq.${distributorId}`
        }, 
        (payload: any) => {
          console.log('🔔 Orders real-time event:', payload.eventType, payload);
          
          // Handle INSERT events (new orders)
          if (payload.eventType === 'INSERT' && payload.new) {
            console.log('🆕 New order detected via real-time:', payload.new.id);
            console.log('Order data:', payload.new);
            // Refresh orders to get the new order with proper joins
            loadOrders();
          }
          
          // Handle UPDATE events (order status changes, etc.)
          if (payload.eventType === 'UPDATE' && payload.new) {
            console.log('✏️ Order update detected via real-time:', payload.new.id);
            // Refresh orders to get updated data with proper joins
            loadOrders();
          }
          
          // Handle DELETE events (if orders are deleted)
          if (payload.eventType === 'DELETE' && payload.old) {
            console.log('🗑️ Order deletion detected via real-time:', payload.old.id);
            // Remove order from local state
            setOrders(prev => prev.filter(order => order.id !== payload.old.id));
          }
        }
      )
      .subscribe((status) => {
        console.log('📡 Orders subscription status:', status);
        if (status === 'SUBSCRIBED') {
          console.log('✅ Successfully subscribed to orders real-time updates');
        } else if (status === 'CHANNEL_ERROR') {
          console.error('❌ Error subscribing to orders channel');
        } else if (status === 'TIMED_OUT') {
          console.error('⏱️ Subscription timed out');
        } else if (status === 'CLOSED') {
          console.log('🔒 Channel closed');
        }
      });
    
    const ordersSubscription = ordersChannel;

    // Set up order_products subscription to detect when products are added/updated
    const orderProductsChannel = supabase.channel(`order_products_changes_${Date.now()}`);
    
    orderProductsChannel
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'order_products'
        }, 
        (payload: any) => {
          console.log('📦 Order products real-time event:', payload.eventType, payload);
          // When order products change, refresh orders to get updated product counts
          loadOrders();
        }
      )
      .subscribe((status) => {
        console.log('📡 Order products subscription status:', status);
        if (status === 'SUBSCRIBED') {
          console.log('✅ Successfully subscribed to order_products real-time updates');
        } else if (status === 'CHANNEL_ERROR') {
          console.error('❌ Error subscribing to order_products channel');
        }
      });
    
    const orderProductsSubscription = orderProductsChannel;

    // Set up customers subscription to detect when customer data changes
    const customersChannel = supabase.channel(`customers_changes_${Date.now()}`);
    
    customersChannel
      .on('postgres_changes', 
        { 
          event: 'UPDATE', 
          schema: 'public', 
          table: 'customers',
          filter: `distributor_id=eq.${distributorId}`
        }, 
        (payload: any) => {
          console.log('👥 Customer update detected via real-time:', payload.new?.id);
          // When customer data changes, refresh orders to get updated customer info
          loadOrders();
        }
      )
      .subscribe((status) => {
        console.log('📡 Customers subscription status:', status);
        if (status === 'SUBSCRIBED') {
          console.log('✅ Successfully subscribed to customers real-time updates');
        } else if (status === 'CHANNEL_ERROR') {
          console.error('❌ Error subscribing to customers channel');
        }
      });
    
    const customersSubscription = customersChannel;

    return () => {
      console.log('🧹 Cleaning up real-time subscriptions...');
      supabase.removeChannel(ordersSubscription);
      supabase.removeChannel(orderProductsSubscription);
      supabase.removeChannel(customersSubscription);
    };
  }, [distributorId, loadOrders]);

  return {
    orders,
    ordersLoading,
    ordersError,
    updateStatus,
    bulkUpdateStatus,
    refreshOrders: () => loadOrders()
  };
}