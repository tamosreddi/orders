'use client';

import { useState, useEffect, useMemo } from 'react';
import { Customer, CustomerFilterState } from '../../types/customer';
import { getCustomers, updateCustomer, createCustomer, CreateCustomerData } from '../../lib/mockCustomers';
import { RowSelectionState } from '@tanstack/react-table';

// Component imports
import { CustomerTable } from '../../components/customer_components/CustomerTable';
import { CustomerTabFilterBar } from '../../components/customer_components/CustomerTabFilterBar';
import { CustomerFilterPopup } from '../../components/customer_components/CustomerFilterPopup';
import { CustomerDetailsPanel } from '../../components/customer_components/CustomerDetailsPanel';
import { InviteCustomerPanel } from '../../components/customer_components/InviteCustomerPanel';
import { TablePagination } from '../../components/TablePagination';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [searchValue, setSearchValue] = useState('');
  const [isFilterPopupOpen, setIsFilterPopupOpen] = useState(false);
  const [isInvitePanelOpen, setIsInvitePanelOpen] = useState(false);
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

  const handleInviteCustomer = async (customerData: CreateCustomerData) => {
    try {
      const newCustomer = await createCustomer(customerData, true); // Send invite
      setCustomers([...customers, newCustomer]);
      
      // Switch to Pending tab to show the new customer
      setFilters(prev => ({ ...prev, tab: 'PENDING' }));
      setCurrentPage(1);
      
      setIsInvitePanelOpen(false);
    } catch (error) {
      console.error('Failed to invite customer:', error);
      throw error;
    }
  };

  const handleSaveCustomer = async (customerData: CreateCustomerData) => {
    try {
      const newCustomer = await createCustomer(customerData, false); // Don't send invite
      setCustomers([...customers, newCustomer]);
      
      // Switch to Active tab to show the saved customer
      setFilters(prev => ({ ...prev, tab: 'ACTIVE' }));
      setCurrentPage(1);
      
      setIsInvitePanelOpen(false);
    } catch (error) {
      console.error('Failed to save customer:', error);
      throw error;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-text-muted">Loading customers...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-0">
      <div className="max-w-container mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-heading-xl font-sans text-primary-ink font-antialiased">
            CUSTOMERS
          </h1>
        </div>

        {/* Tab Filter Bar and Action Buttons */}
        <div className="mb-6">
          <CustomerTabFilterBar
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onFilterPopupOpen={() => setIsFilterPopupOpen(true)}
            onInviteCustomer={() => setIsInvitePanelOpen(true)}
            searchValue={searchValue}
            onSearchChange={handleSearchChange}
          />
        </div>

        {/* Customers Table */}
        <div className="bg-surface-0 rounded-lg shadow-card">
          <CustomerTable
            customers={paginatedCustomers}
            rowSelection={rowSelection}
            onRowSelectionChange={setRowSelection}
            onCustomerSelect={handleCustomerSelect}
          />

          {/* Table Pagination */}
          <TablePagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={setPageSize}
          />
        </div>
      </div>

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

      {/* Invite Customer Panel */}
      <InviteCustomerPanel
        isOpen={isInvitePanelOpen}
        onClose={() => setIsInvitePanelOpen(false)}
        onInviteCustomer={handleInviteCustomer}
        onSaveCustomer={handleSaveCustomer}
      />
    </div>
  );
}