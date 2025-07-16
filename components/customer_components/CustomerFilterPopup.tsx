//used in Customers page to filter the customers

'use client';

import React, { useState } from 'react';
import { X, Calendar } from 'lucide-react';
import { CustomerStatus, CustomerFilterState, PREDEFINED_LABELS } from '../../types/customer';

interface CustomerFilterPopupProps {
  isOpen: boolean;
  onClose: () => void;
  filters: CustomerFilterState;
  onFiltersChange: (filters: CustomerFilterState) => void;
}

export function CustomerFilterPopup({ 
  isOpen, 
  onClose, 
  filters, 
  onFiltersChange 
}: CustomerFilterPopupProps) {
  const [localFilters, setLocalFilters] = useState<CustomerFilterState>(filters);

  if (!isOpen) return null;

  const statusOptions: { value: CustomerStatus; label: string }[] = [
    { value: 'ORDERING', label: 'Ordering' },
    { value: 'AT_RISK', label: 'At risk' },
    { value: 'STOPPED_ORDERING', label: 'Stopped ordering' },
    { value: 'NO_ORDERS_YET', label: 'No orders yet' },
  ];

  const handleStatusChange = (status: CustomerStatus) => {
    const currentStatus = localFilters.status || [];
    const newStatus = currentStatus.includes(status)
      ? currentStatus.filter(s => s !== status)
      : [...currentStatus, status];
    
    setLocalFilters({
      ...localFilters,
      status: newStatus.length > 0 ? newStatus : undefined
    });
  };

  const handleLabelChange = (labelName: string) => {
    const currentLabels = localFilters.labels || [];
    const newLabels = currentLabels.includes(labelName)
      ? currentLabels.filter(l => l !== labelName)
      : [...currentLabels, labelName];
    
    setLocalFilters({
      ...localFilters,
      labels: newLabels.length > 0 ? newLabels : undefined
    });
  };

  const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
    const currentRange = localFilters.dateRange || { start: '', end: '' };
    const newRange = { ...currentRange, [field]: value };
    
    setLocalFilters({
      ...localFilters,
      dateRange: (newRange.start || newRange.end) ? newRange : undefined
    });
  };

  const handleApply = () => {
    onFiltersChange(localFilters);
    onClose();
  };

  const handleClear = () => {
    const clearedFilters = {
      tab: localFilters.tab,
      search: localFilters.search
    };
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96 max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Filter Customers</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Status Filter */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Status</h4>
          <div className="space-y-2">
            {statusOptions.map((option) => (
              <label key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localFilters.status?.includes(option.value) || false}
                  onChange={() => handleStatusChange(option.value)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                />
                <span className="text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Labels Filter */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Labels</h4>
          <div className="space-y-2">
            {PREDEFINED_LABELS.map((label) => (
              <label key={label.name} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localFilters.labels?.includes(label.name) || false}
                  onChange={() => handleLabelChange(label.name)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                />
                <div className="flex items-center">
                  <div
                    className="w-4 h-4 rounded mr-2"
                    style={{ backgroundColor: label.color }}
                  />
                  <span className="text-sm text-gray-700">{label.name}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Date Range Filter */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Date Range</h4>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">From</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="date"
                  value={localFilters.dateRange?.start || ''}
                  onChange={(e) => handleDateRangeChange('start', e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">To</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="date"
                  value={localFilters.dateRange?.end || ''}
                  onChange={(e) => handleDateRangeChange('end', e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between">
          <button
            onClick={handleClear}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Clear all
          </button>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Apply filters
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}