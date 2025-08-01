//used in Customers page to filter the customers as Pending or Active

'use client';

import { ChevronDown, Filter, Search, Plus } from 'lucide-react';
import { CustomerFilterState } from '../../types/customer';

interface CustomerTabFilterBarProps {
  filters: CustomerFilterState;
  onFiltersChange: (filters: CustomerFilterState) => void;
  onFilterPopupOpen: () => void;
  onInviteCustomer: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
}

export function CustomerTabFilterBar({ 
  filters, 
  onFiltersChange, 
  onFilterPopupOpen,
  onInviteCustomer,
  searchValue,
  onSearchChange 
}: CustomerTabFilterBarProps) {
  const handleTabChange = (tab: CustomerFilterState['tab']) => {
    onFiltersChange({
      ...filters,
      tab,
    });
  };

  const tabs = [
    { key: 'ACTIVE' as const, label: 'Active' },
    { key: 'PENDING' as const, label: 'Pending' },
  ];

  return (
    <div className="flex items-center justify-between">
      {/* Left side - Tabs and Search */}
      <div className="flex items-center">
        {/* Tabs */}
        <div className="flex mr-6">
          {tabs.map((tab, index) => {
            const isActive = filters.tab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => handleTabChange(tab.key)}
                className={`
                  px-4 py-2 text-sm font-medium border-b-2 transition-all duration-fast
                  ${isActive 
                    ? 'border-brand-navy-900 text-brand-navy-900' 
                    : 'border-transparent text-text-muted hover:text-text-default hover:border-gray-300'
                  }
                  ${index === 0 ? 'mr-6' : ''}
                `}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Search Bar */}
        <div className="relative mr-2">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search customers..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy-500 focus:border-transparent w-64 transition-all duration-fast"
          />
        </div>
      </div>

      {/* Right side - Filter Buttons and Invite button */}
      <div className="flex items-center space-x-3">
        <button 
          onClick={onFilterPopupOpen}
          className="flex items-center gap-2 px-3 py-2 text-sm text-text-muted border border-gray-300 rounded-md hover:text-text-default hover:border-gray-400 transition-colors"
        >
          <Filter size={16} />
          Filter
          <ChevronDown size={16} />
        </button>
        
        {/* Invite New Customer Button */}
        <button
          onClick={onInviteCustomer}
          className="flex items-center space-x-2 px-4 py-2 bg-state-success text-white rounded-md text-sm font-medium hover:opacity-90 transition-opacity duration-fast"
        >
          <Plus className="h-4 w-4" />
          <span>INVITE NEW CUSTOMER</span>
        </button>
      </div>
    </div>
  );
}