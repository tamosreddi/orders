export interface Order {
  id: string;
  customer: {
    name: string;
    avatar: string;
  };
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  orderDate: string;
  products: number;
  status: 'CONFIRMED' | 'PENDING';
}

export type OrderStatus = 'CONFIRMED' | 'PENDING';
export type OrderChannel = 'WHATSAPP' | 'SMS' | 'EMAIL';

export interface FilterState {
  search: string;
  status: 'ALL' | 'PENDING' | 'CONFIRMED';
}

export interface SortingState {
  id: string;
  desc: boolean;
}[]