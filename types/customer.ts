export interface CustomerLabel {
  id: string;
  name: string;
  color: string;
  value?: string;
}

export interface Customer {
  id: string;
  name: string; // Business name (maps to business_name in DB)
  customerName?: string; // Person responsible for the business (maps to contact_person_name in DB)
  avatar: string; // Maps to avatar_url in DB
  code: string; // Maps to customer_code in DB
  labels: CustomerLabel[];
  lastOrdered: string | null; // Maps to last_ordered_date in DB
  expectedOrder: string | null; // Maps to expected_order_date in DB
  status: CustomerStatus;
  invitationStatus: CustomerInvitationStatus;
  email: string | null;
  phone?: string;
  address?: string;
  joinedDate: string; // Maps to joined_date in DB
  totalOrders: number; // Maps to total_orders in DB
  totalSpent: number; // Maps to total_spent in DB
}

export type CustomerStatus = 'ORDERING' | 'AT_RISK' | 'STOPPED_ORDERING' | 'NO_ORDERS_YET';
export type CustomerInvitationStatus = 'ACTIVE' | 'PENDING';

export interface CustomerFilterState {
  tab: CustomerInvitationStatus;
  search?: string;
  status?: CustomerStatus[];
  labels?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface CustomerSortingState {
  id: string;
  desc: boolean;
}

// Predefined label types
export const PREDEFINED_LABELS = [
  { name: 'Dairy', color: '#FEF3C7' },
  { name: 'Carnes', color: '#FEE2E2' },
  { name: 'Restaurant', color: '#E0F2FE' },
  { name: 'Bar', color: '#F3E8FF' },
] as const;