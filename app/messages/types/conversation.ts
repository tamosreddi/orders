export interface Conversation {
  id: string;
  customerId: string;
  customer: {
    name: string;
    avatar: string;
    code: string;
  };
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  status: 'ACTIVE' | 'ARCHIVED';
  lastMessageAt: string;
  unreadCount: number;
  lastMessage: {
    content: string;
    isFromCustomer: boolean;
  };
  aiContextSummary?: string;
  
  // Multi-tenant isolation
  distributorId: string;
  
  // Metadata
  createdAt: string;
  updatedAt: string;
}

export type ConversationChannel = 'WHATSAPP' | 'SMS' | 'EMAIL';
export type ConversationStatus = 'ACTIVE' | 'ARCHIVED';

export interface ConversationFilterState {
  search?: string;
  channel?: ConversationChannel[];
  status?: ConversationStatus;
  unreadOnly?: boolean;
}

export interface ConversationSortingState {
  id: string;
  desc: boolean;
}

export interface CreateConversationData {
  customerId: string;
  channel: ConversationChannel;
  distributorId: string;
}

export interface UpdateConversationData {
  status?: ConversationStatus;
  aiContextSummary?: string;
  unreadCount?: number;
}