export interface OrderProduct {
  id: string;
  name: string;
  unit: string;
  quantity: number;
  unitPrice: number;
  linePrice: number;
}

export interface OrderMessage {
  id: string;
  content: string;
  timestamp: string;
  isOriginal: boolean;
  isContinuation?: boolean;
  continuationSequence?: number | null;
  intent?: string | null;
}

export interface OrderDetails {
  id: string;
  customer: {
    name: string;
    avatar: string;
    code: string;
    address: string;
  };
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  receivedDate: string;
  receivedTime: string;
  deliveryDate: string;
  postalCode: string;
  products: OrderProduct[];
  totalAmount: number;
  additionalComment: string;
  attachments: string[];
  whatsappMessage: string;
  originalMessage?: {
    id: string;
    content: string;
    timestamp: string;
  } | null;
  allMessages: OrderMessage[];
  status: 'CONFIRMED' | 'PENDING' | 'REVIEW';
}

export interface Order {
  id: string;
  customer: {
    name: string;
    avatar: string;
    code: string;
  };
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  receivedDate: string;
  receivedTime: string;
  deliveryDate: string;
  products: number;
  status: 'CONFIRMED' | 'PENDING' | 'REVIEW';
}

export type OrderStatus = 'CONFIRMED' | 'PENDING' | 'REVIEW';
export type OrderChannel = 'WHATSAPP' | 'SMS' | 'EMAIL';

export interface FilterState {
  tab: 'PENDING' | 'ACCEPTED';
  sortBy?: string;
  filterBy?: string;
}

export interface SortingState {
  id: string;
  desc: boolean;
}[]