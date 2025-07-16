export interface CustomerLabel {
  id: string;
  name: string;
  color: string;
  value?: string;
}

export interface Customer {
  id: string;
  name: string; // Business name
  customerName?: string; // Person responsible for the business
  avatar: string;
  code: string;
  labels: CustomerLabel[];
  lastOrdered: string | null;
  expectedOrder: string | null;
  status: CustomerStatus;
  invitationStatus: CustomerInvitationStatus;
  email: string;
  phone?: string;
  address?: string;
  joinedDate: string;
  totalOrders: number;
  totalSpent: number;
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