export interface MessageAttachment {
  id: string;
  type: string;
  url: string;
  fileName: string;
  fileSize?: number;
  mimeType?: string;
}

export interface Message {
  id: string;
  conversationId: string;
  content: string;
  isFromCustomer: boolean;
  messageType: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT';
  status: 'SENT' | 'DELIVERED' | 'READ';
  attachments?: MessageAttachment[];
  
  // AI Processing Fields
  aiProcessed: boolean;
  aiConfidence?: number;
  aiExtractedIntent?: string;
  aiExtractedProducts?: any[];
  aiSuggestedResponses?: string[];
  
  // Order Context
  orderContextId?: string;
  
  // Multi-tenant isolation
  distributorId: string;
  
  // Metadata
  externalMessageId?: string;
  createdAt: string;
  updatedAt: string;
}

export type MessageType = 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT';
export type MessageStatus = 'SENT' | 'DELIVERED' | 'READ';

export interface AIResponse {
  suggestions: string[];
  confidence: number;
  extractedIntent?: string;
  extractedProducts?: any[];
  error?: string;
}

export interface SendMessageData {
  conversationId: string;
  content: string;
  messageType?: MessageType;
  attachments?: MessageAttachment[];
}