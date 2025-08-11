'use client';

import React, { useState, useEffect } from 'react';
import { X, Calendar } from 'lucide-react';
import { Order } from '../types/order';

interface ConsolidationModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedOrders: Order[];
  onConfirm: (data: { receivedDate: string; deliveryDate: string }) => void;
}

export function ConsolidationModal({ isOpen, onClose, selectedOrders, onConfirm }: ConsolidationModalProps) {
  const [receivedDate, setReceivedDate] = useState('');
  const [deliveryDate, setDeliveryDate] = useState('');

  // Set default values from the most recent selected order
  useEffect(() => {
    if (selectedOrders.length > 0) {
      // Find the most recent order by receivedDate
      const mostRecent = selectedOrders.reduce((latest, current) => {
        const latestDate = new Date(latest.receivedDate);
        const currentDate = new Date(current.receivedDate);
        return currentDate > latestDate ? current : latest;
      });

      setReceivedDate(mostRecent.receivedDate);
      setDeliveryDate(mostRecent.deliveryDate === 'por confirmar' ? '' : mostRecent.deliveryDate);
    }
  }, [selectedOrders]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (receivedDate && deliveryDate) {
      onConfirm({
        receivedDate,
        deliveryDate
      });
    }
  };

  const formatDateForInput = (dateString: string): string => {
    if (!dateString || dateString === 'por confirmar') return '';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    return date.toISOString().split('T')[0];
  };

  const handleReceivedDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setReceivedDate(e.target.value);
  };

  const handleDeliveryDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDeliveryDate(e.target.value);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Consolidar Órdenes
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-4">
              Se consolidarán <span className="font-semibold">{selectedOrders.length}</span> órdenes en una sola orden.
            </p>
          </div>

          {/* Received Date */}
          <div className="mb-6">
            <label htmlFor="receivedDate" className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar size={16} className="inline mr-2" />
              Fecha de Recepción
            </label>
            <input
              type="date"
              id="receivedDate"
              value={formatDateForInput(receivedDate)}
              onChange={handleReceivedDateChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-reddi-navyblue focus:border-transparent"
              required
            />
          </div>

          {/* Delivery Date */}
          <div className="mb-6">
            <label htmlFor="deliveryDate" className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar size={16} className="inline mr-2" />
              Fecha de Entrega
            </label>
            <input
              type="date"
              id="deliveryDate"
              value={formatDateForInput(deliveryDate)}
              onChange={handleDeliveryDateChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-reddi-navyblue focus:border-transparent"
              required
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!receivedDate || !deliveryDate}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                receivedDate && deliveryDate
                  ? 'bg-reddi-navyblue text-white hover:opacity-90'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              Consolidar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}