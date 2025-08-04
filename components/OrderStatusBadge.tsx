'use client';

import { OrderStatus } from '../types/order';

interface OrderStatusBadgeProps {
  status: OrderStatus;
}

export function OrderStatusBadge({ status }: OrderStatusBadgeProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'CONFIRMED':
        return {
          dotColor: 'bg-state-success',
          textColor: 'text-state-success',
          label: 'Aceptada'
        };
      case 'PENDING':
        return {
          dotColor: 'bg-state-warning',
          textColor: 'text-state-warning',
          label: 'Pendiente'
        };
      case 'REVIEW':
        return {
          dotColor: 'bg-reddi-navyblue',
          textColor: 'text-reddi-navyblue',
          label: 'En revisión'
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