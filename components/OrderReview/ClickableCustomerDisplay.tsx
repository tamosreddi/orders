//used in Orders Review page to display the customer details

'use client';

import React, { useState } from 'react';
import { Info } from 'lucide-react';

interface ClickableCustomerDisplayProps {
  customerName: string;
  customerCode: string;
  customerAddress: string;
  onClick: () => void;
  loading?: boolean;
}

export function ClickableCustomerDisplay({
  customerName,
  customerCode,
  customerAddress,
  onClick,
  loading = false
}: ClickableCustomerDisplayProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={`
        w-full px-3 py-2 border border-gray-300 rounded-md text-sm cursor-pointer
        transition-all duration-200 ease-in-out
        hover:bg-gray-50 hover:border-gray-400 hover:shadow-sm
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
        ${loading ? 'pointer-events-none opacity-60' : ''}
      `}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label={`View details for customer ${customerName}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="font-medium text-gray-900">
              {customerName}
            </span>
            <span className="text-gray-500">
              ({customerCode})
            </span>
            {loading && (
              <div className="inline-block w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
            )}
          </div>
          <div className="text-gray-600 mt-0.5">
            {customerAddress}
          </div>
        </div>
        
        <div className={`
          ml-2 transition-opacity duration-200 ease-in-out
          ${isHovered && !loading ? 'opacity-100' : 'opacity-0'}
        `}>
          <Info className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    </div>
  );
}