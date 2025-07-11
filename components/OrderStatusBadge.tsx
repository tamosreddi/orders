'use client';

import { OrderStatus } from '../types/order';

interface OrderStatusBadgeProps {
  status: OrderStatus;
}

export function OrderStatusBadge({ status }: OrderStatusBadgeProps) {
  const isConfirmed = status === 'CONFIRMED';
  
  return (
    <div className="inline-flex items-center space-x-2">
      {/* Status dot */}
      <div className={`w-2 h-2 rounded-full ${
        isConfirmed ? 'bg-state-success' : 'bg-state-warning'
      }`} />
      
      {/* Status text */}
      <span className={`text-caption font-medium ${
        isConfirmed ? 'text-state-success' : 'text-state-warning'
      }`}>
        {isConfirmed ? 'Confirmed' : 'Pending'}
      </span>
    </div>
  );
}