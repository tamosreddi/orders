'use client';

import { Search } from 'lucide-react';
import { FilterState } from '../types/order';

interface SearchFilterBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

export function SearchFilterBar({ filters, onFiltersChange }: SearchFilterBarProps) {
  const handleSearchChange = (value: string) => {
    // Legacy component - functionality moved to TabFilterBar
    console.log('Search functionality moved to TabFilterBar');
  };

  const handleStatusChange = (status: any) => {
    // Legacy component - functionality moved to TabFilterBar  
    console.log('Status filtering moved to TabFilterBar');
  };

  const statusTabs = [
    { key: 'ALL' as const, label: 'All Orders' },
    { key: 'PENDING' as const, label: 'Pending Review' },
    { key: 'CONFIRMED' as const, label: 'Accepted' },
  ];

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-text-muted" />
        </div>
        <input
          type="text"
          placeholder="Search... (Legacy component - use TabFilterBar)"
          value=""
          onChange={(e) => handleSearchChange(e.target.value)}
          className="block w-full pl-10 pr-4 py-3 border border-surface-border rounded-md bg-surface-0 text-text-default placeholder-text-muted focus:ring-2 focus:ring-brand-navy-900 focus:border-brand-navy-900 transition-all duration-fast"
          disabled
        />
      </div>

      {/* Status Filter Tabs */}
      <div className="flex space-x-1 bg-surface-alt p-1 rounded-md">
        {statusTabs.map((tab) => {
          const isActive = false; // Legacy component
          return (
            <button
              key={tab.key}
              onClick={() => handleStatusChange(tab.key)}
              className={`flex-1 px-4 py-2 text-caption font-medium rounded-sm transition-all duration-fast ${
                isActive
                  ? 'bg-surface-0 text-text-default shadow-xs'
                  : 'text-text-muted hover:text-text-default hover:bg-surface-0/50'
              }`}
              disabled
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}