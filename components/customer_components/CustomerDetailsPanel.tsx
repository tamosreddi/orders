//used in Customers page to display the customer details when users click on a row

'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Plus, Trash2, Edit2, Save, XCircle } from 'lucide-react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Customer, CustomerLabel, PREDEFINED_LABELS } from '../../types/customer';
import { CustomerStatusBadge } from './CustomerStatusBadge';
import { updateCustomer, addCustomerLabel, removeCustomerLabel } from '../../lib/api/customers';

interface CustomerDetailsPanelProps {
  customer: Customer | null;
  isOpen: boolean;
  onClose: () => void;
  onCustomerUpdate: (customer: Customer) => void;
}

// EditableField component - moved outside to prevent re-creation
type EditableFieldKey = 'businessName' | 'customerName' | 'email' | 'phone' | 'address' | 'code';

const EditableField = ({ 
  label, 
  value, 
  field, 
  type = 'text',
  isEditing,
  editableData,
  isLoading,
  onFieldChange
}: { 
  label: string; 
  value: string; 
  field: EditableFieldKey; 
  type?: string;
  isEditing: boolean;
  editableData: Record<EditableFieldKey, string>;
  isLoading: boolean;
  onFieldChange: (field: EditableFieldKey, value: string) => void;
}) => (
  <div className="flex justify-between items-center">
    <span className="text-caption text-text-muted">{label}</span>
    {isEditing ? (
      <input
        type={type}
        value={editableData[field] || ''}
        onChange={(e) => onFieldChange(field, e.target.value)}
        className="text-caption text-text-default bg-surface-alt border border-surface-border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand-navy-500 min-w-[240px] text-right"
        disabled={isLoading}
        autoFocus={false}
      />
    ) : (
      <span className="text-caption text-text-default">{value || 'Not provided'}</span>
    )}
  </div>
);

export function CustomerDetailsPanel({ 
  customer, 
  isOpen, 
  onClose, 
  onCustomerUpdate 
}: CustomerDetailsPanelProps) {
  const router = useRouter();
  // Label editing state
  const [isEditingLabels, setIsEditingLabels] = useState(false);
  const [newLabelName, setNewLabelName] = useState('');
  const [newLabelColor, setNewLabelColor] = useState('#FEF3C7');
  const [isLabelLoading, setIsLabelLoading] = useState(false);
  const [labelError, setLabelError] = useState<string | null>(null);
  
  // Customer editing state
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  
  // Editable fields state
  const [editableData, setEditableData] = useState<Record<EditableFieldKey, string>>({
    businessName: '',
    customerName: '',
    email: '',
    phone: '',
    address: '',
    code: ''
  });

  // Initialize editable data when customer changes
  useEffect(() => {
    if (customer) {
      setEditableData({
        businessName: customer.name || '',
        customerName: customer.customerName || '',
        email: customer.email || '',
        phone: customer.phone || '',
        address: customer.address || '',
        code: customer.code || ''
      });
    }
  }, [customer]);

  // Handle ESC key to close panel
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscKey);
      // Prevent body scroll when panel is open
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !customer) return null;

  const handleAddLabel = async () => {
    if (!newLabelName.trim() || !customer) return;

    setIsLabelLoading(true);
    setLabelError(null);

    try {
      // Add label to database
      const newLabel = await addCustomerLabel(customer.id, {
        name: newLabelName.trim(),
        color: newLabelColor,
        value: '10789' // You can modify this or make it dynamic
      });

      // Update local state
      const updatedCustomer = {
        ...customer,
        labels: [...customer.labels, newLabel]
      };

      onCustomerUpdate(updatedCustomer);
      setNewLabelName('');
      setNewLabelColor('#FEF3C7');
      setIsEditingLabels(false);

    } catch (error) {
      console.error('Error adding label:', error);
      console.error('Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
        customerId: customer.id,
        labelData: { name: newLabelName.trim(), color: newLabelColor, value: '10789' }
      });
      setLabelError(error instanceof Error ? error.message : 'Failed to add label');
    } finally {
      setIsLabelLoading(false);
    }
  };

  const handleRemoveLabel = async (labelId: string) => {
    if (!customer) return;

    setIsLabelLoading(true);
    setLabelError(null);

    try {
      // Remove label from database
      await removeCustomerLabel(customer.id, labelId);

      // Update local state
      const updatedCustomer = {
        ...customer,
        labels: customer.labels.filter(label => label.id !== labelId)
      };

      onCustomerUpdate(updatedCustomer);

    } catch (error) {
      console.error('Error removing label:', error);
      setLabelError(error instanceof Error ? error.message : 'Failed to remove label');
    } finally {
      setIsLabelLoading(false);
    }
  };

  // Customer editing handlers
  const handleStartEdit = () => {
    setIsEditing(true);
    setEditError(null);
  };

  const handleCancelEdit = () => {
    if (!customer) return;
    
    setIsEditing(false);
    setEditError(null);
    // Reset to original values
    setEditableData({
      businessName: customer.name || '',
      customerName: customer.customerName || '',
      email: customer.email || '',
      phone: customer.phone || '',
      address: customer.address || '',
      code: customer.code || ''
    });
  };

  const handleSaveEdit = async () => {
    if (!customer) return;

    setIsLoading(true);
    setEditError(null);

    try {
      console.log('🎯 [CustomerDetails] Saving customer edits:', editableData);
      
      // Update customer in database
      await updateCustomer(customer.id, {
        name: editableData.businessName,
        customerName: editableData.customerName,
        email: editableData.email,
        phone: editableData.phone,
        address: editableData.address
      });

      // Update local state
      const updatedCustomer: Customer = {
        ...customer,
        name: editableData.businessName,
        customerName: editableData.customerName,
        email: editableData.email,
        phone: editableData.phone,
        address: editableData.address
      };

      onCustomerUpdate(updatedCustomer);
      setIsEditing(false);
      
      console.log('🎯 [CustomerDetails] Customer updated successfully');
    } catch (error) {
      console.error('🚨 [CustomerDetails] Error updating customer:', error);
      setEditError(error instanceof Error ? error.message : 'Failed to update customer');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFieldChange = (field: EditableFieldKey, value: string) => {
    setEditableData(prev => ({
      ...prev,
      [field]: value
    }));
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

  const handleStartChat = () => {
    if (!customer) return;
    
    // Navigate to messages page with customer parameter
    router.push(`/messages?customer=${customer.id}`);
    
    // Close the customer details panel
    onClose();
  };

  const handleViewOrderHistory = () => {
    if (!customer) return;
    
    // Check if customer has orders
    if (customer.totalOrders === 0) {
      // Simple alert for no orders
      alert('This customer has no orders yet.');
      return;
    }
    
    // Navigate to orders page with customer filter
    router.push(`/orders?customer=${customer.code}`);
    
    // Close the customer details panel
    onClose();
  };

  const panelContent = (
    <div className="fixed inset-0 z-modal">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-medium"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="absolute right-0 top-0 h-full w-full max-w-lg bg-surface-0 shadow-modal transform transition-transform duration-medium flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-surface-border">
          <h2 className="text-2xl font-semibold text-text-default">
            Customer Details
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-text-muted hover:text-text-default transition-colors duration-fast rounded-md hover:bg-surface-alt"
            aria-label="Close customer details"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
          {/* Customer Summary */}
          <div className="space-y-4">
            <div>
              <h3 className="text-body font-semibold text-text-default mb-3">
                Customer Summary
              </h3>
              <div className="flex items-center space-x-3 p-4 bg-surface-alt rounded-lg">
                <Image
                  src={customer.avatar}
                  alt={customer.name}
                  width={48}
                  height={48}
                  className="rounded-full"
                />
                <div>
                  <p className="text-body font-medium text-text-default">
                    {customer.name}
                  </p>
                  <p className="text-caption text-text-muted">
                    {customer.email}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Customer Information */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-body font-semibold text-text-default">
                Customer Information
              </h3>
              {!isEditing && !isEditingLabels && (
                <button
                  onClick={handleStartEdit}
                  className="flex items-center space-x-1 text-xs font-medium bg-gray-100 text-text-default rounded px-3 py-1 shadow-sm border border-gray-300 hover:bg-gray-200 transition-colors duration-fast focus:outline-none focus:ring-2 focus:ring-brand-navy-500"
                  style={{ minHeight: '28px' }}
                >
                  <Edit2 className="h-4 w-4 mr-1" />
                  <span>Edit</span>
                </button>
              )}
            </div>

            {/* Error Messages */}
            {editError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{editError}</p>
              </div>
            )}
            {labelError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{labelError}</p>
              </div>
            )}
            
            <div className="space-y-3">
              {/* Editable Fields */}
              <EditableField 
                label="Business Name" 
                value={customer.name} 
                field="businessName" 
                isEditing={isEditing}
                editableData={editableData}
                isLoading={isLoading}
                onFieldChange={handleFieldChange}
              />
              
              <EditableField 
                label="Contact Person" 
                value={customer.customerName || ''} 
                field="customerName" 
                isEditing={isEditing}
                editableData={editableData}
                isLoading={isLoading}
                onFieldChange={handleFieldChange}
              />
              
              <EditableField 
                label="Email" 
                value={customer.email || ''} 
                field="email" 
                type="email"
                isEditing={isEditing}
                editableData={editableData}
                isLoading={isLoading}
                onFieldChange={handleFieldChange}
              />
              
              <EditableField 
                label="Phone" 
                value={customer.phone || ''} 
                field="phone" 
                type="tel"
                isEditing={isEditing}
                editableData={editableData}
                isLoading={isLoading}
                onFieldChange={handleFieldChange}
              />
              
              <EditableField 
                label="Address" 
                value={customer.address || ''} 
                field="address" 
                isEditing={isEditing}
                editableData={editableData}
                isLoading={isLoading}
                onFieldChange={handleFieldChange}
              />
              
              <div className="flex justify-between items-center">
                <span className="text-caption text-text-muted">Code</span>
                <span className="text-caption text-text-default">{customer.code || 'Not provided'}</span>
              </div>
            </div>
          </div>

          {/* New Business Information Section */}
          <div className="space-y-4 mt-8">
            <h3 className="text-body font-semibold text-text-default">Business Information</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-caption text-text-muted">Status</span>
                <CustomerStatusBadge status={customer.status} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-caption text-text-muted">Total Orders</span>
                <span className="text-caption text-text-default">{customer.totalOrders}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-caption text-text-muted">Total Spent</span>
                <span className="text-caption text-text-default">
                  {formatCurrency(customer.totalSpent)}
                </span>
              </div>
              {customer.lastOrdered && (
                <div className="flex justify-between items-center">
                  <span className="text-caption text-text-muted">Last Order</span>
                  <span className="text-caption text-text-default">
                    {formatDate(customer.lastOrdered)}
                  </span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-caption text-text-muted">Joined</span>
                <span className="text-caption text-text-default">
                  {formatDate(customer.joinedDate)}
                </span>
              </div>
            </div>
          </div>

          {/* Labels Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-body font-semibold text-text-default">Labels</h3>
              <button
                onClick={() => setIsEditingLabels(true)}
                className="text-caption font-medium text-text-default uppercase hover:opacity-90 transition-opacity duration-fast"
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
                  <span className="text-caption font-medium">
                    {label.name}
                    {label.value && (
                      <span className="ml-1 opacity-75">{label.value}</span>
                    )}
                  </span>
                  <button
                    onClick={() => handleRemoveLabel(label.id)}
                    disabled={isLabelLoading}
                    className="text-text-muted hover:text-red-600 transition-colors duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>

            {/* Add Label Form */}
            {isEditingLabels && (
              <div className="mt-3 p-4 bg-surface-alt rounded-lg">
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Label name"
                    value={newLabelName}
                    onChange={(e) => setNewLabelName(e.target.value)}
                    className="w-full px-3 py-2 border border-surface-border rounded-md text-caption focus:outline-none focus:ring-2 focus:ring-brand-navy-500"
                  />
                  <div className="flex space-x-2">
                    {PREDEFINED_LABELS.map((predefinedLabel) => (
                      <button
                        key={predefinedLabel.name}
                        onClick={() => setNewLabelColor(predefinedLabel.color)}
                        className={`w-8 h-8 rounded border-2 transition-colors duration-fast ${
                          newLabelColor === predefinedLabel.color
                            ? 'border-text-default'
                            : 'border-surface-border'
                        }`}
                        style={{ backgroundColor: predefinedLabel.color }}
                      />
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleAddLabel}
                      disabled={isLabelLoading || !newLabelName.trim()}
                      className="flex-1 py-3 px-4 bg-state-success text-white rounded-md font-medium hover:opacity-90 transition-opacity duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLabelLoading ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Adding...</span>
                        </div>
                      ) : (
                        'Add'
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingLabels(false);
                        setNewLabelName('');
                        setNewLabelColor('#FEF3C7');
                        setLabelError(null);
                      }}
                      disabled={isLabelLoading}
                      className="flex-1 py-3 px-4 border border-surface-border text-text-default rounded-md font-medium hover:bg-surface-alt transition-colors duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="space-y-4 pt-4 border-t border-surface-border">
            <div className="space-y-2">
              {isEditing ? (
                // Edit mode buttons
                <>
                  <button 
                    onClick={handleSaveEdit}
                    disabled={isLoading}
                    className="w-full py-3 px-4 bg-blue-600 text-white rounded-md font-medium hover:opacity-90 transition-opacity duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Saving Changes...</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center space-x-2">
                        <Save className="h-4 w-4" />
                        <span>Save Changes</span>
                      </div>
                    )}
                  </button>
                  <button 
                    onClick={handleCancelEdit}
                    disabled={isLoading}
                    className="w-full py-3 px-4 border border-surface-border text-text-default rounded-md font-medium hover:bg-surface-alt transition-colors duration-fast disabled:opacity-50"
                  >
                    <div className="flex items-center justify-center space-x-2">
                      <XCircle className="h-4 w-4" />
                      <span>Cancel</span>
                    </div>
                  </button>
                </>
              ) : (
                // Normal mode buttons
                <>
                  <button 
                    onClick={handleStartChat}
                    className="w-full py-3 px-4 bg-state-success text-white rounded-md font-medium hover:opacity-90 transition-opacity duration-fast"
                  >
                    Start Chat
                  </button>
                  <button 
                    onClick={handleViewOrderHistory}
                    className="w-full py-3 px-4 border border-surface-border text-text-default rounded-md font-medium hover:bg-surface-alt transition-colors duration-fast"
                  >
                    View Order History
                  </button>
                </>
              )}
            </div>
          </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Use portal to render outside of normal DOM hierarchy
  return typeof window !== 'undefined' 
    ? createPortal(panelContent, document.body)
    : null;
}