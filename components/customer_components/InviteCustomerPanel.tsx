//used in Customers page to invite a new customer. Appears when Clcik on INVITE NEW CUSTOMER button

'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Upload, Plus, Trash2, Phone, Mail, ChevronDown, ChevronUp, User } from 'lucide-react';
import Image from 'next/image';
import { CustomerLabel, PREDEFINED_LABELS } from '../../types/customer';

interface ContactData {
  id: string;
  name: string;
  phone: string;
  email: string;
  preferredContact: 'phone' | 'email';
  canPlaceOrders: boolean;
}

interface BusinessData {
  businessName: string;
  businessCode: string;
  businessLocation: string;
  businessLogo: string;
  labels: CustomerLabel[];
  contacts: ContactData[];
}

interface InviteBusinessData extends BusinessData {
  // For backwards compatibility with existing API calls
  customerName: string;
  customerCode: string;
  avatar: string;
  phone: string;
  email: string;
  preferredContact: 'phone' | 'email';
}

interface InviteCustomerPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onInviteCustomer: (customerData: InviteBusinessData) => void;
  onSaveCustomer: (customerData: InviteBusinessData) => void;
}

export function InviteCustomerPanel({ 
  isOpen, 
  onClose, 
  onInviteCustomer,
  onSaveCustomer 
}: InviteCustomerPanelProps) {
  const [businessData, setBusinessData] = useState<BusinessData>({
    businessName: '',
    businessCode: '',
    businessLocation: '',
    businessLogo: '',
    labels: [],
    contacts: [{
      id: 'primary',
      name: '',
      phone: '',
      email: '',
      preferredContact: 'email',
      canPlaceOrders: true
    }]
  });

  const [collapsedSections, setCollapsedSections] = useState({
    businessDetails: false,
    contactInfo: false
  });

  const [isEditingLabels, setIsEditingLabels] = useState(false);
  const [newLabelName, setNewLabelName] = useState('');
  const [newLabelColor, setNewLabelColor] = useState('#FEF3C7');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saveError, setSaveError] = useState<string | null>(null);

  // Generate business code when business name changes
  useEffect(() => {
    if (businessData.businessName && !businessData.businessCode) {
      const code = generateBusinessCode(businessData.businessName);
      setBusinessData(prev => ({ ...prev, businessCode: code }));
    }
  }, [businessData.businessName, businessData.businessCode]);

  // Generate business logo when business name changes
  useEffect(() => {
    if (businessData.businessName && !businessData.businessLogo) {
      const logo = generateBusinessLogo(businessData.businessName);
      setBusinessData(prev => ({ ...prev, businessLogo: logo }));
    }
  }, [businessData.businessName, businessData.businessLogo]);

  // Handle ESC key to close panel
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const generateBusinessCode = (businessName: string): string => {
    const prefix = businessName.substring(0, 3).toUpperCase();
    const randomNum = Math.floor(10000 + Math.random() * 90000);
    return `${prefix}${randomNum}`;
  };

  const generateBusinessLogo = (businessName: string): string => {
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'];
    const seed = businessName.replace(/\s+/g, '').toLowerCase();
    const colorIndex = seed.length % colors.length;
    const backgroundColor = colors[colorIndex];
    const initials = businessName.split(' ').map(word => word.charAt(0)).join('').substring(0, 2).toUpperCase();
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(initials)}&background=${backgroundColor.substring(1)}&color=fff&size=128&bold=true`;
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!businessData.businessName.trim()) {
      newErrors.businessName = 'Business name is required';
    }
    if (!businessData.businessLocation.trim()) {
      newErrors.businessLocation = 'Business location is required';
    }

    // Validate contacts
    const hasValidContact = businessData.contacts.some(contact => {
      if (!contact.name.trim()) {
        newErrors[`contact-${contact.id}-name`] = 'Contact name is required';
        return false;
      }
      if (!contact.phone.trim() && !contact.email.trim()) {
        newErrors[`contact-${contact.id}`] = 'Either phone or email is required';
        return false;
      }
      if (contact.email && !/\S+@\S+\.\S+/.test(contact.email)) {
        newErrors[`contact-${contact.id}-email`] = 'Please enter a valid email address';
        return false;
      }
      return true;
    });

    if (!hasValidContact) {
      newErrors.contacts = 'At least one valid contact is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (action: 'invite' | 'save') => {
    if (!validateForm()) return;

    setIsLoading(true);
    setSaveError(null); // Clear any previous errors
    
    try {
      // Convert to CreateCustomerData format for API compatibility
      const primaryContact = businessData.contacts[0];
      
      console.log('🎯 [InvitePanel] Starting', action, 'operation');
      console.log('🎯 [InvitePanel] Business data:', businessData);
      console.log('🎯 [InvitePanel] Primary contact:', primaryContact);
      
      const customerData: InviteBusinessData = {
        // Business Information (maps to CreateCustomerData)
        businessName: businessData.businessName,
        businessCode: businessData.businessCode,
        businessLocation: businessData.businessLocation,
        businessLogo: businessData.businessLogo,
        labels: businessData.labels,
        contacts: businessData.contacts,
        
        // Primary contact info (for CreateCustomerData compatibility)
        customerName: primaryContact.name,
        phone: primaryContact.phone,
        email: primaryContact.email,
        preferredContact: primaryContact.preferredContact,
        
        // Legacy compatibility fields
        customerCode: businessData.businessCode, // Same as businessCode
        avatar: businessData.businessLogo        // Same as businessLogo
      };

      console.log('🎯 [InvitePanel] Converted customer data:', customerData);

      if (action === 'invite') {
        console.log('🎯 [InvitePanel] Calling onInviteCustomer...');
        await onInviteCustomer(customerData);
      } else {
        console.log('🎯 [InvitePanel] Calling onSaveCustomer...');
        await onSaveCustomer(customerData);
      }
      
      console.log('🎯 [InvitePanel] Operation successful, closing panel...');
      onClose();
      
      // Reset form
      setBusinessData({
        businessName: '',
        businessCode: '',
        businessLocation: '',
        businessLogo: '',
        labels: [],
        contacts: [{
          id: 'primary',
          name: '',
          phone: '',
          email: '',
          preferredContact: 'email',
          canPlaceOrders: true
        }]
      });
      setSaveError(null);
    } catch (error: any) {
      console.error(`🚨 [InvitePanel] Failed to ${action} business:`, error);
      
      // Show user-friendly error message
      let errorMessage = `Failed to ${action} business. Please try again.`;
      
      if (error?.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      setSaveError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddLabel = () => {
    if (!newLabelName.trim()) return;

    const newLabel: CustomerLabel = {
      id: `label-${Date.now()}`,
      name: newLabelName.trim(),
      color: newLabelColor,
    };

    setBusinessData(prev => ({
      ...prev,
      labels: [...prev.labels, newLabel]
    }));
    setNewLabelName('');
    setNewLabelColor('#FEF3C7');
    setIsEditingLabels(false);
  };

  const handleRemoveLabel = (labelId: string) => {
    setBusinessData(prev => ({
      ...prev,
      labels: prev.labels.filter(label => label.id !== labelId)
    }));
  };

  const handleBusinessInputChange = (field: keyof BusinessData, value: string) => {
    setBusinessData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleContactInputChange = (contactId: string, field: keyof ContactData, value: string | boolean) => {
    setBusinessData(prev => ({
      ...prev,
      contacts: prev.contacts.map(contact => 
        contact.id === contactId ? { ...contact, [field]: value } : contact
      )
    }));
    // Clear error when user starts typing
    const errorKey = `contact-${contactId}-${field}`;
    if (errors[errorKey]) {
      setErrors(prev => ({ ...prev, [errorKey]: '' }));
    }
  };

  const addContact = () => {
    const newContact: ContactData = {
      id: `contact-${Date.now()}`,
      name: '',
      phone: '',
      email: '',
      preferredContact: 'email',
      canPlaceOrders: false
    };
    setBusinessData(prev => ({
      ...prev,
      contacts: [...prev.contacts, newContact]
    }));
  };

  const removeContact = (contactId: string) => {
    setBusinessData(prev => ({
      ...prev,
      contacts: prev.contacts.filter(contact => contact.id !== contactId)
    }));
  };

  const toggleSection = (section: keyof typeof collapsedSections) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (!isOpen) return null;

  const panelContent = (
    <div className="fixed inset-0 z-modal">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-medium"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-surface-0 shadow-modal transform transition-transform duration-medium flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-surface-border">
          <h2 className="text-2xl font-semibold text-text-default">
            Add New Business
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-text-muted hover:text-text-default transition-colors duration-fast rounded-md hover:bg-surface-alt"
            aria-label="Close invite panel"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Business Details Section */}
            <div className="space-y-4">
              <button
                onClick={() => toggleSection('businessDetails')}
                className="flex items-center justify-between w-full text-left"
              >
                <h3 className="text-body font-semibold text-text-default">
                  Business Details
                </h3>
                {collapsedSections.businessDetails ? (
                  <ChevronDown className="h-5 w-5 text-text-muted" />
                ) : (
                  <ChevronUp className="h-5 w-5 text-text-muted" />
                )}
              </button>
              
              {!collapsedSections.businessDetails && (
                <div className="space-y-4 pl-4 border-l-2 border-surface-border">
                  {/* Business Logo */}
                  <div className="space-y-4">
                    <h4 className="text-caption font-medium text-text-muted">
                      Business Logo
                    </h4>
                    <div className="flex items-center space-x-4">
                      <div className="relative">
                        <Image
                          src={businessData.businessLogo || '/logos/default-avatar.png'}
                          alt="Business logo"
                          width={64}
                          height={64}
                          className="rounded-lg bg-surface-alt"
                        />
                      </div>
                      <button className="flex items-center space-x-2 px-3 py-2 border border-surface-border text-text-default rounded-md hover:bg-surface-alt transition-colors duration-fast">
                        <Upload className="h-4 w-4" />
                        <span className="text-caption">Upload Logo</span>
                      </button>
                    </div>
                  </div>

                  {/* Business Information */}
                  <div className="space-y-4">
                    {/* Business Name */}
                    <div>
                      <label className="block text-caption text-text-muted mb-2">
                        Business Name *
                      </label>
                      <input
                        type="text"
                        value={businessData.businessName}
                        onChange={(e) => handleBusinessInputChange('businessName', e.target.value)}
                        className={`w-full px-3 py-2 border rounded-md text-caption focus:outline-none focus:ring-2 focus:ring-brand-navy-500 transition-colors duration-fast ${
                          errors.businessName ? 'border-red-500' : 'border-surface-border'
                        }`}
                        placeholder="Enter business name"
                      />
                      {errors.businessName && (
                        <p className="text-red-500 text-xs mt-1">{errors.businessName}</p>
                      )}
                    </div>

                    {/* Business Code */}
                    <div>
                      <label className="block text-caption text-text-muted mb-2">
                        Business Code
                      </label>
                      <input
                        type="text"
                        value={businessData.businessCode}
                        onChange={(e) => handleBusinessInputChange('businessCode', e.target.value)}
                        className="w-full px-3 py-2 border border-surface-border rounded-md text-caption focus:outline-none focus:ring-2 focus:ring-brand-navy-500 transition-colors duration-fast"
                        placeholder="Auto-generated"
                      />
                      <p className="text-xs text-text-muted mt-1">Auto-generated based on business name, but editable</p>
                    </div>

                    {/* Business Location */}
                    <div>
                      <label className="block text-caption text-text-muted mb-2">
                        Business Location *
                      </label>
                      <input
                        type="text"
                        value={businessData.businessLocation}
                        onChange={(e) => handleBusinessInputChange('businessLocation', e.target.value)}
                        className={`w-full px-3 py-2 border rounded-md text-caption focus:outline-none focus:ring-2 focus:ring-brand-navy-500 transition-colors duration-fast ${
                          errors.businessLocation ? 'border-red-500' : 'border-surface-border'
                        }`}
                        placeholder="Enter business location"
                      />
                      {errors.businessLocation && (
                        <p className="text-red-500 text-xs mt-1">{errors.businessLocation}</p>
                      )}
                    </div>
                  </div>

                  {/* Business Labels */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-caption font-medium text-text-muted">Business Labels</h4>
                      <button
                        onClick={() => setIsEditingLabels(true)}
                        className="text-caption font-medium text-text-default uppercase hover:opacity-90 transition-opacity duration-fast"
                      >
                        <Plus className="h-4 w-4 inline mr-1" />
                        Add Label
                      </button>
                    </div>

                    <div className="space-y-2">
                      {businessData.labels.map((label) => (
                        <div
                          key={label.id}
                          className="flex items-center justify-between p-2 rounded"
                          style={{ backgroundColor: label.color }}
                        >
                          <span className="text-caption font-medium">
                            {label.name}
                          </span>
                          <button
                            onClick={() => handleRemoveLabel(label.id)}
                            className="text-text-muted hover:text-red-600 transition-colors duration-fast"
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
                              className="flex-1 py-3 px-4 bg-state-success text-white rounded-md font-medium hover:opacity-90 transition-opacity duration-fast"
                            >
                              Add
                            </button>
                            <button
                              onClick={() => {
                                setIsEditingLabels(false);
                                setNewLabelName('');
                                setNewLabelColor('#FEF3C7');
                              }}
                              className="flex-1 py-3 px-4 border border-surface-border text-text-default rounded-md font-medium hover:bg-surface-alt transition-colors duration-fast"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Contact Information Section */}
            <div className="space-y-4">
              <button
                onClick={() => toggleSection('contactInfo')}
                className="flex items-center justify-between w-full text-left"
              >
                <h3 className="text-body font-semibold text-text-default">
                  Contact Information
                </h3>
                {collapsedSections.contactInfo ? (
                  <ChevronDown className="h-5 w-5 text-text-muted" />
                ) : (
                  <ChevronUp className="h-5 w-5 text-text-muted" />
                )}
              </button>
              
              {!collapsedSections.contactInfo && (
                <div className="space-y-6 pl-4 border-l-2 border-surface-border">
                  {businessData.contacts.map((contact, index) => (
                    <div key={contact.id} className="space-y-4 p-4 bg-surface-alt rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <User className="h-4 w-4 text-text-muted" />
                          <h4 className="text-caption font-medium text-text-default">
                            {index === 0 ? 'Primary Contact' : `Contact ${index + 1}`}
                          </h4>
                        </div>
                        {index > 0 && (
                          <button
                            onClick={() => removeContact(contact.id)}
                            className="text-text-muted hover:text-red-600 transition-colors duration-fast"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>

                      {/* Contact Name */}
                      <div>
                        <label className="block text-caption text-text-muted mb-2">
                          Contact Name *
                        </label>
                        <input
                          type="text"
                          value={contact.name}
                          onChange={(e) => handleContactInputChange(contact.id, 'name', e.target.value)}
                          className={`w-full px-3 py-2 border rounded-md text-caption focus:outline-none focus:ring-2 focus:ring-brand-navy-500 transition-colors duration-fast ${
                            errors[`contact-${contact.id}-name`] ? 'border-red-500' : 'border-surface-border'
                          }`}
                          placeholder="Enter contact name"
                        />
                        {errors[`contact-${contact.id}-name`] && (
                          <p className="text-red-500 text-xs mt-1">{errors[`contact-${contact.id}-name`]}</p>
                        )}
                      </div>

                      {/* Phone */}
                      <div>
                        <label className="flex items-center text-caption text-text-muted mb-2">
                          <Phone className="h-4 w-4 mr-2" />
                          Phone Number (SMS, WhatsApp)
                        </label>
                        <div className="flex items-center space-x-2">
                          <input
                            type="tel"
                            value={contact.phone}
                            onChange={(e) => handleContactInputChange(contact.id, 'phone', e.target.value)}
                            className="flex-1 px-3 py-2 border border-surface-border rounded-md text-caption focus:outline-none focus:ring-2 focus:ring-brand-navy-500 transition-colors duration-fast"
                            placeholder="+1 (555) 123-4567"
                          />
                          <button
                            type="button"
                            onClick={() => handleContactInputChange(contact.id, 'preferredContact', 'phone')}
                            className={`px-3 py-2 text-xs rounded-md transition-colors duration-fast ${
                              contact.preferredContact === 'phone'
                                ? 'bg-state-success text-white'
                                : 'bg-surface-alt text-text-muted hover:bg-surface-border'
                            }`}
                          >
                            Preferred
                          </button>
                        </div>
                      </div>

                      {/* Email */}
                      <div>
                        <label className="flex items-center text-caption text-text-muted mb-2">
                          <Mail className="h-4 w-4 mr-2" />
                          Email Address
                        </label>
                        <div className="flex items-center space-x-2">
                          <input
                            type="email"
                            value={contact.email}
                            onChange={(e) => handleContactInputChange(contact.id, 'email', e.target.value)}
                            className={`flex-1 px-3 py-2 border rounded-md text-caption focus:outline-none focus:ring-2 focus:ring-brand-navy-500 transition-colors duration-fast ${
                              errors[`contact-${contact.id}-email`] ? 'border-red-500' : 'border-surface-border'
                            }`}
                            placeholder="contact@business.com"
                          />
                          <button
                            type="button"
                            onClick={() => handleContactInputChange(contact.id, 'preferredContact', 'email')}
                            className={`px-3 py-2 text-xs rounded-md transition-colors duration-fast ${
                              contact.preferredContact === 'email'
                                ? 'bg-state-success text-white'
                                : 'bg-surface-alt text-text-muted hover:bg-surface-border'
                            }`}
                          >
                            Preferred
                          </button>
                        </div>
                        {errors[`contact-${contact.id}-email`] && (
                          <p className="text-red-500 text-xs mt-1">{errors[`contact-${contact.id}-email`]}</p>
                        )}
                      </div>

                      {/* Can Place Orders */}
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id={`can-place-orders-${contact.id}`}
                          checked={contact.canPlaceOrders}
                          onChange={(e) => handleContactInputChange(contact.id, 'canPlaceOrders', e.target.checked)}
                          className="rounded border-surface-border text-brand-navy-500 focus:ring-brand-navy-500"
                        />
                        <label htmlFor={`can-place-orders-${contact.id}`} className="text-caption text-text-muted">
                          Can place orders
                        </label>
                      </div>

                      {errors[`contact-${contact.id}`] && (
                        <p className="text-red-500 text-xs">{errors[`contact-${contact.id}`]}</p>
                      )}
                    </div>
                  ))}

                  {/* Add Another Contact Button */}
                  <button
                    onClick={addContact}
                    className="flex items-center space-x-2 w-full p-3 border-2 border-dashed border-surface-border rounded-lg text-text-muted hover:border-brand-navy-500 hover:text-brand-navy-500 transition-colors duration-fast"
                  >
                    <Plus className="h-4 w-4" />
                    <span className="text-caption font-medium">Add Another Contact</span>
                  </button>

                  {errors.contacts && (
                    <p className="text-red-500 text-xs">{errors.contacts}</p>
                  )}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="space-y-4 pt-4 border-t border-surface-border">
              <h3 className="text-body font-semibold text-text-default">
                Actions
              </h3>
              
              {/* Error Message */}
              {saveError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <X className="h-4 w-4 text-red-400" />
                    </div>
                    <div className="ml-2">
                      <p className="text-sm text-red-800">{saveError}</p>
                    </div>
                    <button
                      onClick={() => setSaveError(null)}
                      className="ml-auto text-red-400 hover:text-red-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
              
              <div className="space-y-3">
                <button 
                  onClick={() => handleSubmit('invite')}
                  disabled={isLoading}
                  className="w-full py-3 px-4 bg-state-success text-white rounded-md font-medium hover:opacity-90 transition-opacity duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Sending Invitation...' : 'Send Invitation'}
                </button>
                <button 
                  onClick={() => handleSubmit('save')}
                  disabled={isLoading}
                  className="w-full py-3 px-4 bg-blue-600 text-white rounded-md font-medium hover:opacity-90 transition-opacity duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Saving Business...</span>
                    </div>
                  ) : (
                    'Save Business'
                  )}
                </button>
                <button 
                  onClick={onClose}
                  disabled={isLoading}
                  className="w-full py-3 px-4 border border-surface-border text-text-default rounded-md font-medium hover:bg-surface-alt transition-colors duration-fast disabled:opacity-50"
                >
                  Cancel
                </button>
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