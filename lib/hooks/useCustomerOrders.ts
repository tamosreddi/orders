'use client';

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabase/client';

interface CustomerOrderStats {
  totalOrders: number;
  totalSpent: number;
  lastOrderedDate: string | null;
  averageOrderValue: number;
}

interface UseCustomerOrdersReturn {
  orderStats: CustomerOrderStats | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook to fetch real customer order statistics from the database
 * Uses the customers table which has automatically maintained order statistics
 */
export function useCustomerOrders(customerId: string | null): UseCustomerOrdersReturn {
  const [orderStats, setOrderStats] = useState<CustomerOrderStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch customer order statistics
  const fetchOrderStats = useCallback(async () => {
    if (!customerId) {
      setOrderStats(null);
      setLoading(false);
      return;
    }

    try {
      setError(null);

      const { data, error } = await supabase
        .from('customers')
        .select('total_orders, total_spent, last_ordered_date')
        .eq('id', customerId)
        .single();

      if (error) {
        throw new Error(`Failed to fetch customer order stats: ${error.message}`);
      }

      // Calculate average order value
      const totalOrders = data?.total_orders || 0;
      const totalSpent = data?.total_spent || 0;
      const averageOrderValue = totalOrders > 0 ? Math.round(totalSpent / totalOrders) : 0;

      const stats: CustomerOrderStats = {
        totalOrders,
        totalSpent,
        lastOrderedDate: data?.last_ordered_date || null,
        averageOrderValue
      };

      console.log('Customer order stats fetched:', stats);
      setOrderStats(stats);
    } catch (error) {
      console.error('Error fetching customer order stats:', error);
      setError(error instanceof Error ? error.message : 'Unknown error');
      setOrderStats(null);
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  // Initial load
  useEffect(() => {
    fetchOrderStats();
  }, [fetchOrderStats]);

  // Listen for order-related updates
  useEffect(() => {
    if (!customerId) return;

    console.log('Setting up customer order stats subscription...');
    
    const customersSubscription = supabase
      .channel('customer_orders_stats')
      .on('postgres_changes', 
        { 
          event: 'UPDATE', 
          schema: 'public', 
          table: 'customers',
          filter: `id=eq.${customerId}`
        }, 
        (payload) => {
          console.log('Customer stats updated:', payload);
          fetchOrderStats();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(customersSubscription);
    };
  }, [customerId, fetchOrderStats]);

  return {
    orderStats,
    loading,
    error,
    refresh: fetchOrderStats
  };
}