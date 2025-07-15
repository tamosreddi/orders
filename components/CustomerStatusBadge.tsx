import React from 'react';
import { CustomerStatus } from '../types/customer';

interface CustomerStatusBadgeProps {
  status: CustomerStatus;
}

export function CustomerStatusBadge({ status }: CustomerStatusBadgeProps) {
  const getStatusConfig = (status: CustomerStatus) => {
    switch (status) {
      case 'ORDERING':
        return {
          label: 'Ordering',
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          dotColor: 'bg-green-500'
        };
      case 'AT_RISK':
        return {
          label: 'At risk',
          bgColor: 'bg-yellow-100',
          textColor: 'text-yellow-800',
          dotColor: 'bg-yellow-500'
        };
      case 'STOPPED_ORDERING':
        return {
          label: 'Stopped ordering',
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          dotColor: 'bg-red-500'
        };
      case 'NO_ORDERS_YET':
        return {
          label: 'No orders yet',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          dotColor: 'bg-gray-500'
        };
      default:
        return {
          label: 'Unknown',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          dotColor: 'bg-gray-500'
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}>
      <div className={`w-2 h-2 rounded-full mr-1.5 ${config.dotColor}`} />
      {config.label}
    </div>
  );
}