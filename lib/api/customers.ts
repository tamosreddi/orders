import { supabase } from '../supabase/client';
import type { Database } from '../supabase/types';
import { Customer, CustomerLabel } from '../../types/customer';

/**
 * User-friendly error messages for customer operations
 */
export const CUSTOMER_ERROR_MESSAGES = {
  DUPLICATE_EMAIL: 'A customer with this email already exists',
  DUPLICATE_CODE: 'This business code is already in use',
  NETWORK_ERROR: 'Connection failed. Please check your internet and try again',
  VALIDATION_ERROR: 'Please check the highlighted fields',
  UNKNOWN_ERROR: 'Something went wrong. Please try again',
  PERMISSION_DENIED: 'You do not have permission to perform this action',
  CUSTOMER_NOT_FOUND: 'Customer not found'
} as const;

/**
 * Custom error class for customer operations
 */
export class CustomerError extends Error {
  constructor(
    message: string,
    public code: keyof typeof CUSTOMER_ERROR_MESSAGES,
    public originalError?: any
  ) {
    super(message);
    this.name = 'CustomerError';
  }
}

/**
 * Converts Supabase errors to user-friendly CustomerError
 */
function handleSupabaseError(error: any): CustomerError {
  // Handle specific Supabase error codes
  if (error.code === '23505') { // Unique constraint violation
    if (error.constraint?.includes('email')) {
      return new CustomerError(CUSTOMER_ERROR_MESSAGES.DUPLICATE_EMAIL, 'DUPLICATE_EMAIL', error);
    }
    if (error.constraint?.includes('customer_code')) {
      return new CustomerError(CUSTOMER_ERROR_MESSAGES.DUPLICATE_CODE, 'DUPLICATE_CODE', error);
    }
  }
  
  if (error.code === 'PGRST301') { // Permission denied
    return new CustomerError(CUSTOMER_ERROR_MESSAGES.PERMISSION_DENIED, 'PERMISSION_DENIED', error);
  }
  
  if (error.code === 'PGRST116') { // Not found
    return new CustomerError(CUSTOMER_ERROR_MESSAGES.CUSTOMER_NOT_FOUND, 'CUSTOMER_NOT_FOUND', error);
  }
  
  // Network or unknown errors
  return new CustomerError(CUSTOMER_ERROR_MESSAGES.UNKNOWN_ERROR, 'UNKNOWN_ERROR', error);
}

type CustomerRow = Database['public']['Tables']['customers']['Row'];
type CustomerInsert = Database['public']['Tables']['customers']['Insert'];
type CustomerUpdate = Database['public']['Tables']['customers']['Update'];
type CustomerLabelRow = Database['public']['Tables']['customer_labels']['Row'];

/**
 * Development distributor configuration for testing
 */
interface DevDistributor {
  id: string;
  name: string;
  email: string;
}

const DEV_DISTRIBUTORS: DevDistributor[] = [
  { id: '550e8400-e29b-41d4-a716-446655440000', name: 'Acme Foods Distribution', email: 'admin@acmefoods.com' },
  { id: '550e8400-e29b-41d4-a716-446655440001', name: 'Beta Beverages Co.', email: 'owner@betabev.com' }
];

/**
 * Gets the current user's distributor ID from the session
 * For development, we use a placeholder distributor until authentication is implemented
 */
function getCurrentDistributorId(): string {
  // TODO: This should come from useAuth() hook when called from React components
  // For now, return the first development distributor ID for testing
  const currentDistributor = DEV_DISTRIBUTORS[0];
  
  console.log(`🧪 Development Mode: Using distributor "${currentDistributor.name}" (${currentDistributor.id})`);
  
  return currentDistributor.id;
}

/**
 * Converts Supabase customer row to frontend Customer type
 */
function mapSupabaseCustomerToFrontend(
  customerRow: CustomerRow,
  labels: CustomerLabel[] = []
): Customer {
  return {
    id: customerRow.id,
    name: customerRow.business_name,
    customerName: customerRow.contact_person_name || undefined,
    avatar: customerRow.avatar_url || '/logos/default-avatar.png',
    code: customerRow.customer_code,
    labels: labels,
    lastOrdered: customerRow.last_ordered_date,
    expectedOrder: customerRow.expected_order_date,
    status: customerRow.status,
    invitationStatus: customerRow.invitation_status,
    email: customerRow.email,
    phone: customerRow.phone || undefined,
    address: customerRow.address || undefined,
    joinedDate: customerRow.joined_date || customerRow.created_at.split('T')[0],
    totalOrders: customerRow.total_orders,
    totalSpent: customerRow.total_spent
  };
}

/**
 * Gets all customers for the current distributor with their labels
 */
export async function getCustomers(): Promise<Customer[]> {
  try {
    const distributorId = getCurrentDistributorId();

    // Get customers
    const { data: customers, error: customersError } = await supabase
      .from('customers')
      .select('*')
      .eq('distributor_id', distributorId)
      .order('created_at', { ascending: false });

    if (customersError) {
      throw handleSupabaseError(customersError);
    }

    if (!customers || customers.length === 0) {
      return [];
    }

    // Get customer IDs for label lookup
    const customerIds = customers.map(c => c.id);

    // Get labels for all customers
    const { data: labelAssignments, error: labelsError } = await supabase
      .from('customer_label_assignments')
      .select(`
        customer_id,
        value,
        customer_labels (
          id,
          name,
          color
        )
      `)
      .in('customer_id', customerIds);

    if (labelsError) {
      console.warn('Failed to fetch customer labels:', labelsError.message);
    }

    // Group labels by customer ID
    const labelsByCustomer: Record<string, CustomerLabel[]> = {};
    labelAssignments?.forEach(assignment => {
      if (!labelsByCustomer[assignment.customer_id]) {
        labelsByCustomer[assignment.customer_id] = [];
      }
      
      const label = assignment.customer_labels;
      if (label && typeof label === 'object' && 'id' in label) {
        labelsByCustomer[assignment.customer_id].push({
          id: label.id,
          name: label.name,
          color: label.color,
          value: assignment.value || undefined
        });
      }
    });

    // Map to frontend format
    return customers.map(customer => 
      mapSupabaseCustomerToFrontend(customer, labelsByCustomer[customer.id] || [])
    );

  } catch (error) {
    console.error('Error fetching customers:', error);
    if (error instanceof CustomerError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Gets a single customer by ID
 */
export async function getCustomerById(customerId: string): Promise<Customer | null> {
  try {
    const distributorId = getCurrentDistributorId();

    const { data: customer, error: customerError } = await supabase
      .from('customers')
      .select('*')
      .eq('id', customerId)
      .eq('distributor_id', distributorId)
      .single();

    if (customerError) {
      if (customerError.code === 'PGRST116') {
        return null; // Customer not found
      }
      throw handleSupabaseError(customerError);
    }

    // Get labels for this customer
    const { data: labelAssignments, error: labelsError } = await supabase
      .from('customer_label_assignments')
      .select(`
        value,
        customer_labels (
          id,
          name,
          color
        )
      `)
      .eq('customer_id', customerId);

    if (labelsError) {
      console.warn('Failed to fetch customer labels:', labelsError.message);
    }

    const labels: CustomerLabel[] = labelAssignments?.map(assignment => {
      const label = assignment.customer_labels;
      if (label && typeof label === 'object' && 'id' in label) {
        return {
          id: label.id,
          name: label.name,
          color: label.color,
          value: assignment.value || undefined
        };
      }
      return null;
    }).filter(Boolean) as CustomerLabel[] || [];

    return mapSupabaseCustomerToFrontend(customer, labels);

  } catch (error) {
    console.error('Error fetching customer by ID:', error);
    if (error instanceof CustomerError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Gets a customer by their customer code
 */
export async function getCustomerByCode(customerCode: string): Promise<Customer | null> {
  try {
    const distributorId = getCurrentDistributorId();

    const { data: customer, error: customerError } = await supabase
      .from('customers')
      .select('*')
      .eq('customer_code', customerCode)
      .eq('distributor_id', distributorId)
      .single();

    if (customerError) {
      if (customerError.code === 'PGRST116') {
        return null; // Customer not found
      }
      throw handleSupabaseError(customerError);
    }

    // Get labels for this customer  
    const { data: labelAssignments, error: labelsError } = await supabase
      .from('customer_label_assignments')
      .select(`
        value,
        customer_labels (
          id,
          name,
          color
        )
      `)
      .eq('customer_id', customer.id);

    if (labelsError) {
      console.warn('Failed to fetch customer labels:', labelsError.message);
    }

    const labels: CustomerLabel[] = labelAssignments?.map(assignment => {
      const label = assignment.customer_labels;
      if (label && typeof label === 'object' && 'id' in label) {
        return {
          id: label.id,
          name: label.name,
          color: label.color,
          value: assignment.value || undefined
        };
      }
      return null;
    }).filter(Boolean) as CustomerLabel[] || [];

    return mapSupabaseCustomerToFrontend(customer, labels);

  } catch (error) {
    console.error('Error fetching customer by code:', error);
    if (error instanceof CustomerError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Updates an existing customer
 */
export async function updateCustomer(customerId: string, updates: Partial<Customer>): Promise<void> {
  try {
    const distributorId = getCurrentDistributorId();

    // Map frontend updates to database format
    const dbUpdates: CustomerUpdate = {};

    if (updates.name !== undefined) dbUpdates.business_name = updates.name;
    if (updates.customerName !== undefined) dbUpdates.contact_person_name = updates.customerName;
    if (updates.code !== undefined) dbUpdates.customer_code = updates.code;
    if (updates.email !== undefined) dbUpdates.email = updates.email;
    if (updates.phone !== undefined) dbUpdates.phone = updates.phone;
    if (updates.address !== undefined) dbUpdates.address = updates.address;
    if (updates.avatar !== undefined) dbUpdates.avatar_url = updates.avatar;
    if (updates.status !== undefined) dbUpdates.status = updates.status;
    if (updates.invitationStatus !== undefined) dbUpdates.invitation_status = updates.invitationStatus;
    if (updates.lastOrdered !== undefined) dbUpdates.last_ordered_date = updates.lastOrdered;
    if (updates.expectedOrder !== undefined) dbUpdates.expected_order_date = updates.expectedOrder;
    if (updates.totalOrders !== undefined) dbUpdates.total_orders = updates.totalOrders;
    if (updates.totalSpent !== undefined) dbUpdates.total_spent = updates.totalSpent;

    const { error } = await supabase
      .from('customers')
      .update(dbUpdates)
      .eq('id', customerId)
      .eq('distributor_id', distributorId);

    if (error) {
      throw handleSupabaseError(error);
    }

    // TODO: Handle label updates if needed

  } catch (error) {
    console.error('Error updating customer:', error);
    if (error instanceof CustomerError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Contact data structure matching InviteCustomerPanel
 */
export interface ContactData {
  id: string;
  name: string;
  phone: string;
  email: string;
  preferredContact: 'phone' | 'email';
  canPlaceOrders: boolean;
}

/**
 * Enhanced data structure for creating new customers
 * Matches InviteCustomerPanel's InviteBusinessData structure
 */
export interface CreateCustomerData {
  // Business Information
  businessName: string;
  businessCode: string;
  businessLocation: string;
  businessLogo: string;
  
  // Contact Information (from InviteCustomerPanel contacts array)
  customerName: string;  // Primary contact name
  phone: string;         // Primary contact phone
  email: string;         // Primary contact email
  preferredContact: 'phone' | 'email';
  
  // Legacy compatibility field
  avatar: string;        // Same as businessLogo
  customerCode: string;  // Same as businessCode
  
  // Additional data
  labels: CustomerLabel[];
  
  // Future enhancement: store all contacts
  contacts?: ContactData[];
}

/**
 * Adds a label to a customer
 */
export async function addCustomerLabel(
  customerId: string, 
  labelData: { name: string; color: string; value?: string }
): Promise<CustomerLabel> {
  try {
    const distributorId = getCurrentDistributorId();

    // First, create or find the label
    let labelId: string;
    
    // Try to find existing label with same name (constraint is on name only)
    const { data: existingLabel, error: findError } = await supabase
      .from('customer_labels')
      .select('id, color')
      .eq('name', labelData.name)
      .single();

    if (findError && findError.code !== 'PGRST116') {
      throw handleSupabaseError(findError);
    }

    if (existingLabel) {
      labelId = existingLabel.id;
      // Use the existing label's color if it exists
      labelData.color = existingLabel.color;
    } else {
      // Create new label
      const { data: newLabel, error: labelError } = await supabase
        .from('customer_labels')
        .insert({
          distributor_id: distributorId,
          name: labelData.name,
          color: labelData.color,
          description: null,
          is_predefined: false
        })
        .select()
        .single();

      if (labelError) {
        throw handleSupabaseError(labelError);
      }

      labelId = newLabel.id;
    }

    // Check if assignment already exists
    const { data: existingAssignment } = await supabase
      .from('customer_label_assignments')
      .select('*')
      .eq('customer_id', customerId)
      .eq('label_id', labelId)
      .single();

    if (existingAssignment) {
      // Assignment already exists, just return the label
      return {
        id: labelId,
        name: labelData.name,
        color: labelData.color,
        value: existingAssignment.value || undefined
      };
    }

    // Create the assignment
    const { error: assignmentError } = await supabase
      .from('customer_label_assignments')
      .insert({
        customer_id: customerId,
        label_id: labelId,
        value: labelData.value || null
      });

    if (assignmentError) {
      throw handleSupabaseError(assignmentError);
    }

    return {
      id: labelId,
      name: labelData.name,
      color: labelData.color,
      value: labelData.value
    };

  } catch (error) {
    console.error('Error adding customer label:', error);
    console.error('API Error details:', {
      customerId,
      labelData,
      distributorId: getCurrentDistributorId(),
      error: error
    });
    if (error instanceof CustomerError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Removes a label from a customer
 */
export async function removeCustomerLabel(customerId: string, labelId: string): Promise<void> {
  try {
    const { error } = await supabase
      .from('customer_label_assignments')
      .delete()
      .eq('customer_id', customerId)
      .eq('label_id', labelId);

    if (error) {
      throw handleSupabaseError(error);
    }

  } catch (error) {
    console.error('Error removing customer label:', error);
    if (error instanceof CustomerError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Gets all available labels for the current distributor
 */
export async function getCustomerLabels(): Promise<CustomerLabel[]> {
  try {
    const distributorId = getCurrentDistributorId();

    const { data: labels, error } = await supabase
      .from('customer_labels')
      .select('id, name, color, description')
      .eq('distributor_id', distributorId)
      .order('name');

    if (error) {
      throw handleSupabaseError(error);
    }

    return labels?.map(label => ({
      id: label.id,
      name: label.name,
      color: label.color,
      value: undefined // Labels don't have values until assigned to customers
    })) || [];

  } catch (error) {
    console.error('Error fetching customer labels:', error);
    if (error instanceof CustomerError) {
      throw error;
    }
    throw handleSupabaseError(error);
  }
}

/**
 * Creates a new customer with labels
 */
export async function createCustomer(
  customerData: CreateCustomerData, 
  shouldSendInvite: boolean = true
): Promise<Customer> {
  try {
    console.log('🎯 [API] createCustomer called with:', customerData);
    console.log('🎯 [API] shouldSendInvite:', shouldSendInvite);
    
    const distributorId = getCurrentDistributorId();
    console.log('🎯 [API] Using distributor ID:', distributorId);

    // Prepare customer data for insertion
    const customerInsert: CustomerInsert = {
      distributor_id: distributorId,
      business_name: customerData.businessName,
      contact_person_name: customerData.customerName,
      customer_code: customerData.businessCode, // Use businessCode (more consistent)
      email: customerData.email,
      phone: customerData.phone || null,
      address: customerData.businessLocation,
      avatar_url: customerData.businessLogo, // Use businessLogo (more descriptive)
      status: 'NO_ORDERS_YET',
      invitation_status: shouldSendInvite ? 'PENDING' : 'ACTIVE',
      joined_date: new Date().toISOString(),
      total_orders: 0,
      total_spent: 0
    };

    console.log('🎯 [API] customerInsert prepared:', customerInsert);
    console.log('🎯 [API] customerInsert JSON:', JSON.stringify(customerInsert, null, 2));

    // Insert customer
    console.log('🎯 [API] Inserting customer into database...');
    const { data: newCustomer, error: customerError } = await supabase
      .from('customers')
      .insert(customerInsert)
      .select()
      .single();

    if (customerError) {
      console.error('🚨 [API] Customer insert failed:', customerError);
      throw handleSupabaseError(customerError);
    }

    console.log('🎯 [API] Customer inserted successfully:', newCustomer);

    // Handle labels if provided
    const processedLabels: CustomerLabel[] = [];
    
    if (customerData.labels && customerData.labels.length > 0) {
      for (const label of customerData.labels) {
        try {
          // First, try to find existing label or create new one
          let labelId = label.id;
          
          // If label doesn't have a valid ID or starts with 'label-', it's a new label
          if (!labelId || labelId.startsWith('label-')) {
            // Create new label
            const { data: newLabel, error: labelError } = await supabase
              .from('customer_labels')
              .insert({
                distributor_id: distributorId,
                name: label.name,
                color: label.color,
                description: null,
                is_predefined: false
              })
              .select()
              .single();

            if (labelError) {
              console.warn(`Failed to create label "${label.name}":`, labelError.message);
              continue;
            }

            labelId = newLabel.id;
          }

          // Assign label to customer
          const { error: assignmentError } = await supabase
            .from('customer_label_assignments')
            .insert({
              customer_id: newCustomer.id,
              label_id: labelId,
              value: label.value || null
            });

          if (assignmentError) {
            console.warn(`Failed to assign label "${label.name}" to customer:`, assignmentError.message);
            continue;
          }

          processedLabels.push({
            id: labelId,
            name: label.name,
            color: label.color,
            value: label.value
          });

        } catch (labelError) {
          console.warn(`Error processing label "${label.name}":`, labelError);
        }
      }
    }

    // TODO: Send invitation email if shouldSendInvite is true

    return mapSupabaseCustomerToFrontend(newCustomer, processedLabels);

  } catch (error) {
    console.error('Error creating customer:', error);
    
    // If it's already a CustomerError, just re-throw it
    if (error instanceof CustomerError) {
      throw error;
    }
    
    // Convert other errors to CustomerError
    throw handleSupabaseError(error);
  }
}