'use client';

import { ChevronDown, Filter, Search, Plus } from 'lucide-react';
import { CustomerFilterState } from '../types/customer';

interface CustomerTabFilterBarProps {
  filters: CustomerFilterState;
  onFiltersChange: (filters: CustomerFilterState) => void;
  onFilterPopupOpen: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
}

export function CustomerTabFilterBar({ 
  filters, 
  onFiltersChange, 
  onFilterPopupOpen,
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
    <div className="flex items-center justify-between mb-6">
      {/* Left side - Tabs */}
      <div className="flex mr-6">
        {tabs.map((tab, index) => {
          const isActive = filters.tab === tab.key;
          const showBadge = tab.key === 'PENDING';
          
          return (
            <button
              key={tab.key}
              onClick={() => handleTabChange(tab.key)}
              className={`
                relative px-4 py-2 text-sm font-medium transition-colors
                ${isActive 
                  ? 'text-blue-600 border-b-2 border-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
                }
                ${index > 0 ? 'ml-6' : ''}
              `}
            >
              {tab.label}
              {showBadge && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  2
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Right side - Search, Filter, and Invite button */}
      <div className="flex items-center space-x-4">
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search or filter customers..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-64"
          />
        </div>

        {/* Filter Dropdown */}
        <button
          onClick={onFilterPopupOpen}
          className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <Filter className="h-4 w-4" />
          <span>Filter customers</span>
          <ChevronDown className="h-4 w-4" />
        </button>

        {/* Invite New Customer Button */}
        <button
          disabled
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="h-4 w-4" />
          <span>INVITE NEW CUSTOMER</span>
        </button>
      </div>
    </div>
  );
}