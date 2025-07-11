'use client';

import { useState, useEffect } from 'react';
import { Order, FilterState } from '../../types/order';
import { getOrders } from '../../lib/mockOrders';

// Component imports - these will be implemented in subsequent tasks
import { OrderTable } from '../../components/OrderTable';
import { SearchFilterBar } from '../../components/SearchFilterBar';
import { OrderDrawer } from '../../components/OrderDrawer';

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    status: 'ALL'
  });

  // Load orders on component mount
  useEffect(() => {
    const loadOrders = async () => {
      try {
        const ordersData = await getOrders();
        setOrders(ordersData);
        setFilteredOrders(ordersData);
      } catch (error) {
        console.error('Failed to load orders:', error);
      } finally {
        setLoading(false);
      }
    };

    loadOrders();
  }, []);

  // Filter orders based on search and status
  useEffect(() => {
    let filtered = orders;

    // Apply search filter
    if (filters.search) {
      filtered = filtered.filter(order =>
        order.customer.name.toLowerCase().includes(filters.search.toLowerCase()) ||
        order.id.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    // Apply status filter
    if (filters.status !== 'ALL') {
      filtered = filtered.filter(order => order.status === filters.status);
    }

    setFilteredOrders(filtered);
  }, [orders, filters]);

  const handleRowClick = (order: Order) => {
    setSelectedOrder(order);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
    setSelectedOrder(null);
  };

  const handleBulkConfirm = (selectedOrderIds: string[]) => {
    console.log('Bulk confirming orders:', selectedOrderIds);
    // TODO: Implement actual bulk confirmation with Supabase
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-text-muted">Loading orders...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-0">
      <div className="max-w-container mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-heading-xl font-sans text-primary-ink font-antialiased">
            ORDERS
          </h1>
        </div>

        {/* Search and Filter Bar */}
        <div className="mb-6">
          <SearchFilterBar
            filters={filters}
            onFiltersChange={setFilters}
          />
        </div>

        {/* Orders Table */}
        <div className="bg-surface-0 rounded-lg shadow-card">
          <OrderTable
            orders={filteredOrders}
            onRowClick={handleRowClick}
            onBulkConfirm={handleBulkConfirm}
          />
        </div>

        {/* Order Drawer */}
        <OrderDrawer
          order={selectedOrder}
          isOpen={isDrawerOpen}
          onClose={handleCloseDrawer}
        />
      </div>
    </div>
  );
}