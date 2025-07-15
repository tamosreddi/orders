'use client';

import { useState, useEffect, useMemo } from 'react';
import { Customer, CustomerFilterState } from '../../types/customer';
import { getCustomers, updateCustomer } from '../../lib/mockCustomers';
import { RowSelectionState } from '@tanstack/react-table';

// Component imports
import { CustomerTable } from '../../components/CustomerTable';
import { CustomerTabFilterBar } from '../../components/CustomerTabFilterBar';
import { CustomerFilterPopup } from '../../components/CustomerFilterPopup';
import { CustomerDetailsPanel } from '../../components/CustomerDetailsPanel';
import { TablePagination } from '../../components/TablePagination';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [searchValue, setSearchValue] = useState('');
  const [isFilterPopupOpen, setIsFilterPopupOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [filters, setFilters] = useState<CustomerFilterState>({
    tab: 'ACTIVE',
    search: ''
  });

  // Load customers on component mount
  useEffect(() => {
    const loadCustomers = async () => {
      try {
        const customersData = await getCustomers();
        setCustomers(customersData);
      } catch (error) {
        console.error('Failed to load customers:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCustomers();
  }, []);

  // Filter customers based on filters and search
  const filteredCustomers = useMemo(() => {
    let filtered = customers;

    // Apply tab filter
    if (filters.tab === 'ACTIVE') {
      filtered = filtered.filter(customer => customer.invitationStatus === 'ACTIVE');
    } else if (filters.tab === 'PENDING') {
      filtered = filtered.filter(customer => customer.invitationStatus === 'PENDING');
    }

    // Apply search filter
    if (searchValue.trim()) {
      const searchTerm = searchValue.toLowerCase();
      filtered = filtered.filter(customer =>
        customer.name.toLowerCase().includes(searchTerm) ||
        customer.email.toLowerCase().includes(searchTerm) ||
        customer.code.toLowerCase().includes(searchTerm)
      );
    }

    // Apply advanced filters
    if (filters.status && filters.status.length > 0) {
      filtered = filtered.filter(customer => filters.status!.includes(customer.status));
    }

    if (filters.labels && filters.labels.length > 0) {
      filtered = filtered.filter(customer =>
        customer.labels.some(label => filters.labels!.includes(label.name))
      );
    }

    if (filters.dateRange) {
      const { start, end } = filters.dateRange;
      if (start || end) {
        filtered = filtered.filter(customer => {
          if (!customer.lastOrdered) return false;
          const orderDate = new Date(customer.lastOrdered);
          const startDate = start ? new Date(start) : new Date(0);
          const endDate = end ? new Date(end) : new Date();
          return orderDate >= startDate && orderDate <= endDate;
        });
      }
    }

    return filtered;
  }, [customers, filters, searchValue]);

  // Paginate customers
  const paginatedCustomers = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredCustomers.slice(startIndex, endIndex);
  }, [filteredCustomers, currentPage, pageSize]);

  // Calculate pagination info
  const totalPages = Math.ceil(filteredCustomers.length / pageSize);
  const totalItems = filteredCustomers.length;

  const handleCustomerSelect = (customer: Customer) => {
    setSelectedCustomer(customer);
  };

  const handleCustomerUpdate = async (updatedCustomer: Customer) => {
    try {
      await updateCustomer(updatedCustomer.id, updatedCustomer);
      setCustomers(customers.map(c => 
        c.id === updatedCustomer.id ? updatedCustomer : c
      ));
      setSelectedCustomer(updatedCustomer);
    } catch (error) {
      console.error('Failed to update customer:', error);
    }
  };

  const handleFiltersChange = (newFilters: CustomerFilterState) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleSearchChange = (value: string) => {
    setSearchValue(value);
    setCurrentPage(1); // Reset to first page when search changes
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading customers...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CUSTOMERS</h1>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          <span>Customers synced</span>
        </div>
      </div>

      {/* Filters */}
      <CustomerTabFilterBar
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onFilterPopupOpen={() => setIsFilterPopupOpen(true)}
        searchValue={searchValue}
        onSearchChange={handleSearchChange}
      />

      {/* Table */}
      <div className="bg-white rounded-lg shadow">
        <CustomerTable
          customers={paginatedCustomers}
          rowSelection={rowSelection}
          onRowSelectionChange={setRowSelection}
          onCustomerSelect={handleCustomerSelect}
        />
      </div>

      {/* Pagination */}
      <TablePagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        totalItems={totalItems}
        onPageChange={setCurrentPage}
        onPageSizeChange={setPageSize}
      />

      {/* Filter Popup */}
      <CustomerFilterPopup
        isOpen={isFilterPopupOpen}
        onClose={() => setIsFilterPopupOpen(false)}
        filters={filters}
        onFiltersChange={handleFiltersChange}
      />

      {/* Customer Details Panel */}
      <CustomerDetailsPanel
        customer={selectedCustomer}
        isOpen={!!selectedCustomer}
        onClose={() => setSelectedCustomer(null)}
        onCustomerUpdate={handleCustomerUpdate}
      />
    </div>
  );
}