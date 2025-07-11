'use client';

import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import Image from 'next/image';
import { X } from 'lucide-react';
import { Order } from '../types/order';
import { OrderStatusBadge } from './OrderStatusBadge';

interface OrderDrawerProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
}

export function OrderDrawer({ order, isOpen, onClose }: OrderDrawerProps) {
  // Handle ESC key to close drawer
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscKey);
      // Prevent body scroll when drawer is open
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !order) return null;

  const drawerContent = (
    <div className="fixed inset-0 z-modal">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-medium"
        onClick={onClose}
      />
      
      {/* Drawer Panel */}
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-surface-0 shadow-modal transform transition-transform duration-medium">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-surface-border">
          <h2 className="text-body-lg font-semibold text-text-default">
            Order Details
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-text-muted hover:text-text-default transition-colors duration-fast rounded-md hover:bg-surface-alt"
            aria-label="Close order details"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto h-full">
          {/* Order Summary */}
          <div className="space-y-4">
            <div>
              <h3 className="text-body font-semibold text-text-default mb-3">
                Order Summary
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-caption text-text-muted">Order ID</span>
                  <span className="text-body font-medium text-text-default">{order.id}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-caption text-text-muted">Status</span>
                  <OrderStatusBadge status={order.status} />
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-caption text-text-muted">Order Date</span>
                  <span className="text-body text-text-default">
                    {new Date(order.orderDate).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-caption text-text-muted">Channel</span>
                  <span className="text-caption font-medium text-text-default uppercase">
                    {order.channel}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-caption text-text-muted">Products</span>
                  <span className="text-body font-medium text-text-default">
                    {order.products} item{order.products !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Customer Information */}
          <div className="space-y-4">
            <h3 className="text-body font-semibold text-text-default">
              Customer Information
            </h3>
            <div className="flex items-center space-x-3 p-4 bg-surface-alt rounded-lg">
              <Image
                src={order.customer.avatar}
                alt={order.customer.name}
                width={48}
                height={48}
                className="rounded-full"
              />
              <div>
                <p className="text-body font-medium text-text-default">
                  {order.customer.name}
                </p>
                <p className="text-caption text-text-muted">
                  via {order.channel}
                </p>
              </div>
            </div>
          </div>

          {/* Placeholder for Order Items */}
          <div className="space-y-4">
            <h3 className="text-body font-semibold text-text-default">
              Order Items
            </h3>
            <div className="p-4 bg-surface-alt rounded-lg text-center">
              <p className="text-caption text-text-muted">
                Order items will be displayed here
              </p>
              <p className="text-caption text-text-muted mt-1">
                (To be implemented in future versions)
              </p>
            </div>
          </div>

          {/* Placeholder for Actions */}
          <div className="space-y-4 pt-4 border-t border-surface-border">
            <h3 className="text-body font-semibold text-text-default">
              Actions
            </h3>
            <div className="space-y-2">
              <button className="w-full py-3 px-4 bg-state-success text-white rounded-md font-medium hover:opacity-90 transition-opacity duration-fast">
                Confirm Order
              </button>
              <button className="w-full py-3 px-4 border border-surface-border text-text-default rounded-md font-medium hover:bg-surface-alt transition-colors duration-fast">
                View Full Details
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Use portal to render outside of normal DOM hierarchy
  return typeof window !== 'undefined' 
    ? createPortal(drawerContent, document.body)
    : null;
}