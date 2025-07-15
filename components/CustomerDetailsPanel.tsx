'use client';

import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2 } from 'lucide-react';
import Image from 'next/image';
import { Customer, CustomerLabel, PREDEFINED_LABELS } from '../types/customer';
import { CustomerStatusBadge } from './CustomerStatusBadge';

interface CustomerDetailsPanelProps {
  customer: Customer | null;
  isOpen: boolean;
  onClose: () => void;
  onCustomerUpdate: (customer: Customer) => void;
}

export function CustomerDetailsPanel({ 
  customer, 
  isOpen, 
  onClose, 
  onCustomerUpdate 
}: CustomerDetailsPanelProps) {
  const [isEditingLabels, setIsEditingLabels] = useState(false);
  const [newLabelName, setNewLabelName] = useState('');
  const [newLabelColor, setNewLabelColor] = useState('#FEF3C7');

  if (!isOpen || !customer) return null;

  const handleAddLabel = () => {
    if (!newLabelName.trim()) return;

    const newLabel: CustomerLabel = {
      id: `label-${Date.now()}`,
      name: newLabelName.trim(),
      color: newLabelColor,
      value: '10789'
    };

    const updatedCustomer = {
      ...customer,
      labels: [...customer.labels, newLabel]
    };

    onCustomerUpdate(updatedCustomer);
    setNewLabelName('');
    setNewLabelColor('#FEF3C7');
    setIsEditingLabels(false);
  };

  const handleRemoveLabel = (labelId: string) => {
    const updatedCustomer = {
      ...customer,
      labels: customer.labels.filter(label => label.id !== labelId)
    };
    onCustomerUpdate(updatedCustomer);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl z-50 overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Customer Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Customer Info */}
        <div className="mb-6">
          <div className="flex items-center space-x-4 mb-4">
            <div className="relative">
              <Image
                src={customer.avatar}
                alt={customer.name}
                width={64}
                height={64}
                className="rounded-full"
              />
              <div className="absolute -top-2 -right-2 bg-white border border-gray-200 rounded px-2 py-1 text-xs font-medium text-gray-600">
                {customer.code}
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{customer.name}</h3>
              <p className="text-sm text-gray-600">{customer.email}</p>
              {customer.phone && (
                <p className="text-sm text-gray-600">{customer.phone}</p>
              )}
            </div>
          </div>

          <div className="mb-4">
            <CustomerStatusBadge status={customer.status} />
          </div>

          {customer.address && (
            <div className="mb-4">
              <p className="text-sm text-gray-600">{customer.address}</p>
            </div>
          )}
        </div>

        {/* Labels Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-700">Labels</h4>
            <button
              onClick={() => setIsEditingLabels(true)}
              className="text-blue-600 hover:text-blue-700 text-sm"
            >
              <Plus className="h-4 w-4 inline mr-1" />
              Add Label
            </button>
          </div>

          <div className="space-y-2">
            {customer.labels.map((label) => (
              <div
                key={label.id}
                className="flex items-center justify-between p-2 rounded"
                style={{ backgroundColor: label.color }}
              >
                <span className="text-sm font-medium">
                  {label.name}
                  {label.value && (
                    <span className="ml-1 opacity-75">{label.value}</span>
                  )}
                </span>
                <button
                  onClick={() => handleRemoveLabel(label.id)}
                  className="text-gray-600 hover:text-red-600"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>

          {/* Add Label Form */}
          {isEditingLabels && (
            <div className="mt-3 p-3 border border-gray-200 rounded-lg">
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Label name"
                  value={newLabelName}
                  onChange={(e) => setNewLabelName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex space-x-2">
                  {PREDEFINED_LABELS.map((predefinedLabel) => (
                    <button
                      key={predefinedLabel.name}
                      onClick={() => setNewLabelColor(predefinedLabel.color)}
                      className={`w-8 h-8 rounded border-2 ${
                        newLabelColor === predefinedLabel.color
                          ? 'border-gray-400'
                          : 'border-gray-200'
                      }`}
                      style={{ backgroundColor: predefinedLabel.color }}
                    />
                  ))}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handleAddLabel}
                    className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => {
                      setIsEditingLabels(false);
                      setNewLabelName('');
                      setNewLabelColor('#FEF3C7');
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Order History */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Order History</h4>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Total Orders:</span>
              <span className="font-medium">{customer.totalOrders}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Total Spent:</span>
              <span className="font-medium">{formatCurrency(customer.totalSpent)}</span>
            </div>
            {customer.lastOrdered && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Last Order:</span>
                <span className="font-medium">{formatDate(customer.lastOrdered)}</span>
              </div>
            )}
            {customer.expectedOrder && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Expected Order:</span>
                <span className="font-medium">{formatDate(customer.expectedOrder)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Account Info */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Account Information</h4>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Joined:</span>
              <span className="font-medium">{formatDate(customer.joinedDate)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Status:</span>
              <span className="font-medium capitalize">{customer.invitationStatus.toLowerCase()}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="border-t pt-4">
          <button
            disabled
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send Message
          </button>
        </div>
      </div>
    </div>
  );
}