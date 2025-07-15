'use client';

import { ChevronDown, Filter, ArrowUpDown } from 'lucide-react';
import { FilterState } from '../types/order';

interface TabFilterBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

export function TabFilterBar({ filters, onFiltersChange }: TabFilterBarProps) {
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

      {/* Filter Buttons */}
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