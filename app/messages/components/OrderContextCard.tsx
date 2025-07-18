'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShoppingCart, Calendar, Package, CheckCircle, Clock, AlertCircle, Eye, Edit } from 'lucide-react';
import { Message } from '../types/message';

interface OrderContextData {
  id: string;
  orderNumber: string;
  status: 'CONFIRMED' | 'PENDING' | 'REVIEW' | 'DELIVERED' | 'CANCELLED';
  totalAmount: number;
  productCount: number;
  deliveryDate?: string;
  createdAt: string;
  aiGenerated?: boolean;
  aiConfidence?: number;
}

interface OrderContextCardProps {
  message: Message;
  orderData?: OrderContextData;
  aiExtractedProducts?: any[];
  isInline?: boolean;
  onCreateOrder?: () => void;
  onViewOrder?: (orderId: string) => void;
}

export function OrderContextCard({ 
  message, 
  orderData,
  aiExtractedProducts,
  isInline = true,
  onCreateOrder,
  onViewOrder
}: OrderContextCardProps) {
  const router = useRouter();
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CONFIRMED':
      case 'DELIVERED':
        return 'bg-state-success text-white';
      case 'PENDING':
        return 'bg-state-warning text-white';
      case 'REVIEW':
        return 'bg-brand-navy-900 text-white';
      case 'CANCELLED':
        return 'bg-state-error text-white';
      default:
        return 'bg-surface-alt text-text-default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'CONFIRMED':
      case 'DELIVERED':
        return <CheckCircle className="w-4 h-4" />;
      case 'PENDING':
        return <Clock className="w-4 h-4" />;
      case 'REVIEW':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  const handleCreateOrder = () => {
    if (!aiExtractedProducts) return;
    
    // Navigate to order creation with pre-populated data
    const orderParams = new URLSearchParams({
      source: 'message',
      messageId: message.id,
      conversationId: message.conversationId,
      products: JSON.stringify(aiExtractedProducts)
    });
    
    router.push(`/orders/create?${orderParams.toString()}`);
    onCreateOrder?.();
  };

  const handleViewOrder = () => {
    if (orderData) {
      router.push(`/orders/${orderData.id}`);
      onViewOrder?.(orderData.id);
    }
  };

  const handleEditOrder = () => {
    if (orderData) {
      router.push(`/orders/${orderData.id}/edit`);
    }
  };

  // AI-detected order case
  if (aiExtractedProducts && aiExtractedProducts.length > 0 && !orderData) {
    return (
      <div className={`${isInline ? 'my-3' : ''} bg-blue-50 border border-blue-200 rounded-lg p-4`}>
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <ShoppingCart className="w-4 h-4 text-blue-600" />
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-blue-900">
                Order Detected
              </h4>
              {message.aiConfidence && (
                <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                  AI: {Math.round(message.aiConfidence * 100)}%
                </span>
              )}
            </div>
            
            <div className="text-sm text-blue-700 mb-3">
              <p>AI detected {aiExtractedProducts.length} product{aiExtractedProducts.length !== 1 ? 's' : ''} in this message</p>
            </div>
            
            {/* Expandable product preview */}
            <div className="mb-3">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-xs text-blue-600 hover:text-blue-800 underline"
              >
                {isExpanded ? 'Hide' : 'Show'} detected products
              </button>
              
              {isExpanded && (
                <div className="mt-2 space-y-1">
                  {aiExtractedProducts.slice(0, 3).map((product, index) => (
                    <div key={index} className="text-xs bg-white rounded p-2 border border-blue-100">
                      <div className="flex justify-between">
                        <span className="font-medium">{product.name}</span>
                        <span>{product.quantity} {product.unit}</span>
                      </div>
                      {product.unit_price && (
                        <div className="text-blue-600 mt-1">
                          ${product.unit_price} per {product.unit}
                        </div>
                      )}
                    </div>
                  ))}
                  {aiExtractedProducts.length > 3 && (
                    <div className="text-xs text-blue-600">
                      +{aiExtractedProducts.length - 3} more products
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={handleCreateOrder}
                className="flex-1 px-3 py-2 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors flex items-center justify-center space-x-1"
              >
                <ShoppingCart className="w-3 h-3" />
                <span>Create Order</span>
              </button>
              <button className="px-3 py-2 border border-blue-300 text-blue-600 text-xs rounded hover:bg-blue-50 transition-colors">
                Ignore
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Existing order case
  if (orderData) {
    return (
      <div className={`${isInline ? 'my-3' : ''} bg-surface-alt border border-border-subtle rounded-lg p-4`}>
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-brand-navy-900 rounded-lg flex items-center justify-center">
              <Package className="w-4 h-4 text-white" />
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-text-default">
                Order #{orderData.orderNumber}
              </h4>
              <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getStatusColor(orderData.status)}`}>
                {getStatusIcon(orderData.status)}
                <span>{orderData.status}</span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm mb-3">
              <div>
                <div className="text-text-muted text-xs">Total Amount</div>
                <div className="font-medium">${orderData.totalAmount.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-text-muted text-xs">Products</div>
                <div className="font-medium">{orderData.productCount} items</div>
              </div>
              {orderData.deliveryDate && (
                <div className="col-span-2">
                  <div className="text-text-muted text-xs flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>Delivery Date</span>
                  </div>
                  <div className="font-medium">
                    {new Date(orderData.deliveryDate).toLocaleDateString()}
                  </div>
                </div>
              )}
            </div>
            
            {orderData.aiGenerated && (
              <div className="mb-3 p-2 bg-blue-50 rounded text-xs">
                <div className="flex items-center space-x-1 text-blue-700">
                  <span>🤖 AI-Generated Order</span>
                  {orderData.aiConfidence && (
                    <span className="text-blue-600">
                      • {Math.round(orderData.aiConfidence * 100)}% confidence
                    </span>
                  )}
                </div>
              </div>
            )}
            
            <div className="flex space-x-2">
              <button
                onClick={handleViewOrder}
                className="flex-1 px-3 py-2 bg-brand-navy-900 text-white text-xs rounded hover:bg-brand-navy-700 transition-colors flex items-center justify-center space-x-1"
              >
                <Eye className="w-3 h-3" />
                <span>View Details</span>
              </button>
              {(orderData.status === 'PENDING' || orderData.status === 'REVIEW') && (
                <button
                  onClick={handleEditOrder}
                  className="px-3 py-2 border border-border-subtle text-text-default text-xs rounded hover:bg-surface-alt transition-colors flex items-center space-x-1"
                >
                  <Edit className="w-3 h-3" />
                  <span>Edit</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Fallback - no order data
  return null;
}