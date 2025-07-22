import { supabase } from './client';
import type { Database } from './types';
import { Customer, CustomerLabel } from '../../types/customer';

type CustomerRow = Database['public']['Tables']['customers']['Row'];
type CustomerInsert = Database['public']['Tables']['customers']['Insert'];
type CustomerUpdate = Database['public']['Tables']['customers']['Update'];
type CustomerLabelRow = Database['public']['Tables']['customer_labels']['Row'];

/**
 * Gets the current user's distributor ID from the session
 * For now, we'll use a default distributor until authentication is fully implemented
 */
function getCurrentDistributorId(): string {
  // TODO: This should come from useAuth() hook when called from React components
  // For now, return a default distributor ID for testing
  return 'default-distributor-id';
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
      throw new Error(`Failed to fetch customers: ${customersError.message}`);
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
    throw error;
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
      throw new Error(`Failed to fetch customer: ${customerError.message}`);
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
    throw error;
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
      throw new Error(`Failed to fetch customer: ${customerError.message}`);
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
    throw error;
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
      throw new Error(`Failed to update customer: ${error.message}`);
    }

    // TODO: Handle label updates if needed

  } catch (error) {
    console.error('Error updating customer:', error);
    throw error;
  }
}

/**
 * Data structure for creating new customers
 */
export interface CreateCustomerData {
  customerName: string;
  businessName: string;
  businessLocation: string;
  phone: string;
  email: string;
  preferredContact: 'phone' | 'email';
  customerCode: string;
  avatar: string;
  labels: CustomerLabel[];
}

/**
 * Creates a new customer with labels
 */
export async function createCustomer(
  customerData: CreateCustomerData, 
  shouldSendInvite: boolean = true
): Promise<Customer> {
  try {
    const distributorId = getCurrentDistributorId();

    // Prepare customer data for insertion
    const customerInsert: CustomerInsert = {
      distributor_id: distributorId,
      business_name: customerData.businessName,
      contact_person_name: customerData.customerName,
      customer_code: customerData.customerCode,
      email: customerData.email,
      phone: customerData.phone || null,
      address: customerData.businessLocation,
      avatar_url: customerData.avatar,
      status: 'NO_ORDERS_YET',
      invitation_status: shouldSendInvite ? 'PENDING' : 'ACTIVE',
      joined_date: new Date().toISOString().split('T')[0],
      total_orders: 0,
      total_spent: 0
    };

    // Insert customer
    const { data: newCustomer, error: customerError } = await supabase
      .from('customers')
      .insert(customerInsert)
      .select()
      .single();

    if (customerError) {
      throw new Error(`Failed to create customer: ${customerError.message}`);
    }

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
    throw error;
  }
}