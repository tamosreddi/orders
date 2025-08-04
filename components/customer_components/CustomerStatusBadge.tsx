//used in Customers page, in the table,  to display the customer status

import React from 'react';
import { CustomerStatus } from '../../types/customer';

interface CustomerStatusBadgeProps {
  status: CustomerStatus;
}

export function CustomerStatusBadge({ status }: CustomerStatusBadgeProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'ORDERING':
        return {
          dotColor: 'bg-state-success',
          textColor: 'text-state-success',
          label: 'Ordenando'
        };
      case 'AT_RISK':
        return {
          dotColor: 'bg-state-warning',
          textColor: 'text-state-warning',
          label: 'En riesgo'
        };
      case 'STOPPED_ORDERING':
        return {
          dotColor: 'bg-red-500',
          textColor: 'text-red-500',
          label: 'Dejó de ordenar'
        };
      case 'NO_ORDERS_YET':
        return {
          dotColor: 'bg-gray-400',
          textColor: 'text-gray-400',
          label: 'Sin órdenes aún'
        };
      default:
        return {
          dotColor: 'bg-gray-400',
          textColor: 'text-gray-400',
          label: status
        };
    }
  };

  const styles = getStatusStyles();
  
  return (
    <div className="inline-flex items-center space-x-2">
      {/* Status dot */}
      <div className={`w-2 h-2 rounded-full ${styles.dotColor}`} />
      
      {/* Status text */}
      <span className={`text-sm font-medium ${styles.textColor}`}>
        {styles.label}
      </span>
    </div>
  );
}