'use client';

import { ChevronDown, Filter, ArrowUpDown, Search } from 'lucide-react';
import { FilterState } from '../types/order';

interface TabFilterBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
}

export function TabFilterBar({ filters, onFiltersChange, searchValue, onSearchChange }: TabFilterBarProps) {
  const handleTabChange = (tab: FilterState['tab']) => {
    onFiltersChange({
      ...filters,
      tab,
    });
  };

  const tabs = [
    { key: 'PENDING' as const, label: 'Pending' },
    { key: 'ACCEPTED' as const, label: 'Accepted' },
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
        <div className="relative mr-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search orders..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy-500 focus:border-transparent w-64 transition-all duration-fast"
          />
        </div>
      </div>

      {/* Right side - Filter Buttons */}
      <div className="flex items-center space-x-3">
        <button className="flex items-center gap-2 px-3 py-2 text-sm text-text-muted border border-gray-300 rounded-md hover:text-text-default hover:border-gray-400 transition-colors">
          <Filter size={16} />
          Filter
          <ChevronDown size={16} />
        </button>
        
        <button className="flex items-center gap-2 px-3 py-2 text-sm text-text-muted border border-gray-300 rounded-md hover:text-text-default hover:border-gray-400 transition-colors">
          <ArrowUpDown size={16} />
          Sort by
          <ChevronDown size={16} />
        </button>
      </div>
    </div>
  );
}