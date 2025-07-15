'use client';

import { useState, useEffect, useMemo } from 'react';
import { Order, FilterState } from '../../types/order';
import { getOrders } from '../../lib/mockOrders';
import { RowSelectionState } from '@tanstack/react-table';

// Component imports
import { OrderTable } from '../../components/OrderTable';
import { TabFilterBar } from '../../components/TabFilterBar';
import { OrderActionButtons } from '../../components/OrderActionButtons';
import { TablePagination } from '../../components/TablePagination';

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<FilterState>({
    tab: 'PENDING'
  });

  // Load orders on component mount
  useEffect(() => {
    const loadOrders = async () => {
      try {
        const ordersData = await getOrders();
        setOrders(ordersData);
      } catch (error) {
        console.error('Failed to load orders:', error);
      } finally {
        setLoading(false);
      }
    };

    loadOrders();
  }, []);

  // Filter orders based on tab selection
  const filteredOrders = useMemo(() => {
    let filtered = orders;

    // Apply tab filter
    if (filters.tab === 'PENDING') {
      filtered = filtered.filter(order => order.status === 'PENDING' || order.status === 'REVIEW');
    } else if (filters.tab === 'ACCEPTED') {
      filtered = filtered.filter(order => order.status === 'CONFIRMED');
    }

    return filtered;
  }, [orders, filters.tab]);

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

  // Reset selection and page when filters change
  useEffect(() => {
    setRowSelection({});
    setCurrentPage(1);
  }, [filters.tab]);

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

  const handleConfirm = (orderIds: string[]) => {
    console.log('Confirming orders:', orderIds);
    // TODO: Implement confirm functionality with Supabase
    setRowSelection({});
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
            ORDERS
          </h1>
        </div>

        {/* Tab Filter Bar and Action Buttons */}
        <div className="mb-6 flex items-start justify-between">
          <TabFilterBar
            filters={filters}
            onFiltersChange={setFilters}
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