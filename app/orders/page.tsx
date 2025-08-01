'use client';

import { useState, useEffect, useMemo, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Order, FilterState } from '../../types/order';
import { OrderError } from '../../lib/api/orders';
import { RowSelectionState } from '@tanstack/react-table';
import { useOrders } from './hooks/useOrders';

// Component imports
import { OrderTable } from '../../components/OrderTable';
import { TabFilterBar } from '../../components/TabFilterBar';
import { OrderActionButtons } from '../../components/OrderActionButtons';
import { TablePagination } from '../../components/TablePagination';

function OrdersContent() {
  const searchParams = useSearchParams();
  
  // Use the orders hook for real-time updates
  const { 
    orders, 
    ordersLoading: loading, 
    ordersError,
    updateStatus,
    bulkUpdateStatus 
  } = useOrders({ 
    distributorId: '550e8400-e29b-41d4-a716-446655440000' // TODO: Get from auth
  });
  
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [searchValue, setSearchValue] = useState('');
  const [filters, setFilters] = useState<FilterState>({
    tab: 'PENDING'
  });
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Show notification and auto-hide after 5 seconds
  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  // Handle orders error from the hook
  if (ordersError && !notification) {
    showNotification('error', ordersError);
  }

  // Filter orders based on tab selection and search
  const filteredOrders = useMemo(() => {
    let filtered = orders;

    // Apply customer filter from URL parameter
    const customerParam = searchParams.get('customer');
    if (customerParam) {
      filtered = filtered.filter(order => 
        order.customer.code === customerParam
      );
    }

    // Apply tab filter
    if (filters.tab === 'PENDING') {
      filtered = filtered.filter(order => order.status === 'PENDING' || order.status === 'REVIEW');
    } else if (filters.tab === 'ACCEPTED') {
      filtered = filtered.filter(order => order.status === 'CONFIRMED');
    }

    // Apply search filter
    if (searchValue.trim()) {
      const searchTerm = searchValue.toLowerCase();
      filtered = filtered.filter(order =>
        order.customer.name.toLowerCase().includes(searchTerm) ||
        order.customer.code.toLowerCase().includes(searchTerm) ||
        order.id.toLowerCase().includes(searchTerm) ||
        order.channel.toLowerCase().includes(searchTerm)
      );
    }

    return filtered;
  }, [orders, filters.tab, searchValue, searchParams]);

  // Paginated orders
  const paginatedOrders = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredOrders.slice(startIndex, endIndex);
  }, [filteredOrders, currentPage, pageSize]);

  // Selected orders for action buttons
  const selectedOrders = useMemo(() => {
    return Object.keys(rowSelection)
      .filter(key => rowSelection[key])
      .map(index => paginatedOrders[parseInt(index)])
      .filter(Boolean);
  }, [rowSelection, paginatedOrders]);

  // Calculate pagination info
  const totalPages = Math.ceil(filteredOrders.length / pageSize);

  // Reset selection and page when filters or search change
  useEffect(() => {
    setRowSelection({});
    setCurrentPage(1);
  }, [filters.tab, searchValue]);

  const handleSearchChange = (value: string) => {
    setSearchValue(value);
  };

  // Action handlers
  const handleDelete = (orderIds: string[]) => {
    console.log('Deleting orders:', orderIds);
    // TODO: Implement delete functionality
    setRowSelection({});
  };

  const handleUpload = (orderIds: string[]) => {
    console.log('Uploading orders:', orderIds);
    // TODO: Implement upload functionality
    setRowSelection({});
  };

  const handleConfirm = async (orderIds: string[]) => {
    try {
      if (orderIds.length === 1) {
        await updateStatus(orderIds[0], 'CONFIRMED');
        showNotification('success', 'Order confirmed successfully!');
      } else {
        await bulkUpdateStatus(orderIds, 'CONFIRMED');
        showNotification('success', `${orderIds.length} orders confirmed successfully!`);
      }
      
      setRowSelection({});
    } catch (error) {
      console.error('Failed to confirm orders:', error);
      if (error instanceof OrderError) {
        showNotification('error', error.message);
      } else {
        showNotification('error', 'Failed to confirm orders. Please try again.');
      }
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    setRowSelection({}); // Reset selection when changing pages
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1);
    setRowSelection({});
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
            ÓRDENES
          </h1>
        </div>

        {/* Notification */}
        {notification && (
          <div className={`mb-6 p-4 rounded-md ${
            notification.type === 'success' 
              ? 'bg-green-50 border border-green-200 text-green-800' 
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{notification.message}</span>
              <button 
                onClick={() => setNotification(null)}
                className="ml-4 text-gray-400 hover:text-gray-600"
                aria-label="Close notification"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Tab Filter Bar and Action Buttons */}
        <div className="mb-6 flex items-start justify-between">
          <TabFilterBar
            filters={filters}
            onFiltersChange={setFilters}
            searchValue={searchValue}
            onSearchChange={handleSearchChange}
          />
          <OrderActionButtons
            selectedOrders={selectedOrders}
            onDelete={handleDelete}
            onUpload={handleUpload}
            onConfirm={handleConfirm}
          />
        </div>

        {/* Orders Table */}
        <div className="bg-surface-0 rounded-lg shadow-card">
          <OrderTable
            orders={paginatedOrders}
            rowSelection={rowSelection}
            onRowSelectionChange={setRowSelection}
          />

          {/* Table Pagination */}
          <TablePagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={filteredOrders.length}
            pageSize={pageSize}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        </div>
      </div>
    </div>
  );
}

export default function OrdersPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading orders...</div>}>
      <OrdersContent />
    </Suspense>
  );
}