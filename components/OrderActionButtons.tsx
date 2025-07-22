'use client';

import { Trash2, Upload, Check } from 'lucide-react';
import { Order } from '../types/order';

interface OrderActionButtonsProps {
  selectedOrders: Order[];
  onDelete: (orderIds: string[]) => void;
  onUpload: (orderIds: string[]) => void;
  onConfirm: (orderIds: string[]) => void;
}

export function OrderActionButtons({ 
  selectedOrders, 
  onDelete, 
  onUpload, 
  onConfirm 
}: OrderActionButtonsProps) {
  const hasSelection = selectedOrders.length > 0;
  const hasUnconfirmedSelection = selectedOrders.some(order => order.status !== 'CONFIRMED');
  const selectedOrderIds = selectedOrders.map(order => order.id);

  return (
    <div className="flex items-center space-x-2">
      {/* Delete and Upload Buttons */}
      <button
        onClick={() => onDelete(selectedOrderIds)}
        disabled={!hasSelection}
        className={`
          p-2 rounded-md transition-all duration-fast
          ${hasSelection
            ? 'text-red-600 hover:bg-red-50 border border-red-200'
            : 'text-gray-400 cursor-not-allowed border border-gray-200'
          }
        `}
        title="Delete"
      >
        <Trash2 size={16} />
      </button>

      <button
        onClick={() => onUpload(selectedOrderIds)}
        disabled={!hasSelection}
        className={`
          p-2 rounded-md transition-all duration-fast
          ${hasSelection
            ? 'text-blue-600 hover:bg-blue-50 border border-blue-200'
            : 'text-gray-400 cursor-not-allowed border border-gray-200'
          }
        `}
        title="Upload"
      >
        <Upload size={16} />
      </button>

      {/* Confirm Order Button */}
      <button
        onClick={() => onConfirm(selectedOrderIds)}
        disabled={!hasSelection || !hasUnconfirmedSelection}
        className={`
          px-4 py-2 text-sm font-medium rounded-md transition-all duration-fast
          ${hasSelection && hasUnconfirmedSelection
            ? 'bg-state-success text-white hover:opacity-90'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }
        `}
      >
        <Check size={16} className="inline mr-2" />
        Confirmar orden
      </button>
    </div>
  );
}