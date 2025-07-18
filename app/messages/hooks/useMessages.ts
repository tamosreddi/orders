'use client';

import { useState, useEffect, useCallback } from 'react';
// Mock Supabase client for demonstration
// In production, this would be: import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
// Mock data for demonstration
const mockConversations = [
  {
    id: '1',
    customer_id: 'customer_1',
    channel: 'WHATSAPP',
    status: 'ACTIVE',
    last_message_at: new Date().toISOString(),
    unread_count: 2,
    ai_context_summary: null,
    distributor_id: 'dist_123',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    customers: {
      id: 'customer_1',
      business_name: 'Chez Aimee',
      customer_code: 'C001',
      avatar_url: null
    },
    messages: [{
      content: 'I need to place an order for tomorrow',
      is_from_customer: true
    }]
  },
  {
    id: '2',
    customer_id: 'customer_2',
    channel: 'EMAIL',
    status: 'ACTIVE',
    last_message_at: new Date(Date.now() - 3600000).toISOString(),
    unread_count: 0,
    ai_context_summary: null,
    distributor_id: 'dist_123',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    customers: {
      id: 'customer_2',
      business_name: 'Restaurant Paolo',
      customer_code: 'C002',
      avatar_url: null
    },
    messages: [{
      content: 'Thank you for the delivery!',
      is_from_customer: true
    }]
  }
];

const mockMessages = [
  {
    id: '1',
    conversation_id: '1',
    content: 'Hello! I need to place an order for tomorrow.',
    is_from_customer: true,
    message_type: 'TEXT',
    status: 'READ',
    attachments: [],
    ai_processed: false,
    ai_confidence: null,
    ai_extracted_intent: null,
    ai_extracted_products: null,
    ai_suggested_responses: null,
    order_context_id: null,
    external_message_id: null,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: '2',
    conversation_id: '1',
    content: 'Of course! What would you like to order?',
    is_from_customer: false,
    message_type: 'TEXT',
    status: 'READ',
    attachments: [],
    ai_processed: false,
    ai_confidence: null,
    ai_extracted_intent: null,
    ai_extracted_products: null,
    ai_suggested_responses: null,
    order_context_id: null,
    external_message_id: null,
    created_at: new Date(Date.now() - 1800000).toISOString(),
    updated_at: new Date(Date.now() - 1800000).toISOString()
  }
];

const createMockSupabaseClient = (): any => {
  console.log('Creating mock Supabase client');
  
  return {
    from: (table: string) => {
      console.log(`Mock client: from(${table})`);
      
      const mockChain = {
        select: (...args: any[]) => {
          console.log(`Mock client: select called on ${table}`, args);
          return mockChain;
        },
        eq: (...args: any[]) => {
          console.log(`Mock client: eq called on ${table}`, args);
          return mockChain;
        },
        order: (...args: any[]) => {
          console.log(`Mock client: order called on ${table}, returning data`);
          
          // Return mock data based on table
          if (table === 'conversations') {
            return Promise.resolve({ data: mockConversations, error: null });
          } else if (table === 'messages') {
            return Promise.resolve({ data: mockMessages, error: null });
          }
          return Promise.resolve({ data: [], error: null });
        },
        insert: (data: any) => {
          console.log(`Mock client: insert called on ${table}`, data);
          return {
            select: () => ({
              single: () => Promise.resolve({ 
                data: { id: `mock-${Date.now()}`, ...data[0] }, 
                error: null 
              })
            })
          };
        },
        update: (data: any) => {
          console.log(`Mock client: update called on ${table}`, data);
          return mockChain;
        },
        in: (column: string, values: any[]) => {
          console.log(`Mock client: in called on ${table}`, column, values);
          return Promise.resolve({ data: [], error: null });
        }
      };
      
      return mockChain;
    },
    channel: (name: string) => {
      console.log(`Mock client: channel(${name})`);
      return {
        on: (event: string, options: any, callback: Function) => ({
          subscribe: () => {
            console.log(`Mock client: subscribed to ${name}`);
            return { unsubscribe: () => console.log(`Mock client: unsubscribed from ${name}`) };
          }
        })
      };
    },
    removeChannel: (channel: any) => {
      console.log('Mock client: removeChannel called');
    }
  };
};
import { Conversation } from '../types/conversation';
import { Message, SendMessageData } from '../types/message';

interface UseMessagesOptions {
  distributorId: string;
  conversationId?: string | null;
}

interface UseMessagesReturn {
  // Conversations
  conversations: Conversation[];
  conversationsLoading: boolean;
  conversationsError: string | null;
  
  // Messages
  messages: Message[];
  messagesLoading: boolean;
  messagesError: string | null;
  
  // Actions
  sendMessage: (data: SendMessageData) => Promise<void>;
  markAsRead: (messageIds: string[]) => Promise<void>;
  createConversation: (customerId: string, channel: 'WHATSAPP' | 'SMS' | 'EMAIL') => Promise<string>;
  archiveConversation: (conversationId: string) => Promise<void>;
  
  // Real-time
  refreshConversations: () => Promise<void>;
  refreshMessages: () => Promise<void>;
}

// Create the mock client once outside the hook to avoid recreation
const mockSupabaseClient = createMockSupabaseClient();

export function useMessages({ distributorId, conversationId }: UseMessagesOptions): UseMessagesReturn {
  const supabase = mockSupabaseClient;
  
  // Transform mock data to frontend format for immediate display
  const initialConversations: Conversation[] = mockConversations.map((conv: any) => ({
    id: conv.id,
    customerId: conv.customer_id,
    customer: {
      name: conv.customers.business_name,
      avatar: conv.customers.avatar_url || '',
      code: conv.customers.customer_code
    },
    channel: conv.channel,
    status: conv.status,
    lastMessageAt: conv.last_message_at,
    unreadCount: conv.unread_count || 0,
    lastMessage: conv.messages?.[0] ? {
      content: conv.messages[0].content,
      isFromCustomer: conv.messages[0].is_from_customer
    } : {
      content: '',
      isFromCustomer: false
    },
    aiContextSummary: conv.ai_context_summary,
    distributorId: conv.distributor_id,
    createdAt: conv.created_at,
    updatedAt: conv.updated_at
  }));

  // Conversations state
  const [conversations, setConversations] = useState<Conversation[]>(initialConversations);
  const [conversationsLoading, setConversationsLoading] = useState(false); // Start as false for debugging
  const [conversationsError, setConversationsError] = useState<string | null>(null);
  
  // Messages state
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  // Load conversations with RLS filtering
  const loadConversations = useCallback(async () => {
    try {
      console.log('loadConversations: Starting...');
      setConversationsLoading(true);
      setConversationsError(null);

      console.log('loadConversations: Making query...');
      const { data, error } = await supabase
        .from('conversations')
        .select(`
          id,
          customer_id,
          channel,
          status,
          last_message_at,
          unread_count,
          ai_context_summary,
          distributor_id,
          created_at,
          updated_at,
          customers!inner (
            id,
            business_name,
            customer_code,
            avatar_url
          ),
          messages!conversations_last_message_fkey (
            content,
            is_from_customer
          )
        `)
        .eq('distributor_id', distributorId)
        .eq('status', 'ACTIVE')
        .order('last_message_at', { ascending: false });

      console.log('loadConversations: Query result:', { data, error });

      if (error) {
        throw new Error(`Failed to load conversations: ${(error as any)?.message || 'Unknown error'}`);
      }

      // Transform data to match frontend interface
      const transformedConversations: Conversation[] = (data || []).map((conv: any) => ({
        id: conv.id,
        customerId: conv.customer_id,
        customer: {
          name: conv.customers.business_name,
          avatar: conv.customers.avatar_url || '',
          code: conv.customers.customer_code
        },
        channel: conv.channel,
        status: conv.status,
        lastMessageAt: conv.last_message_at,
        unreadCount: conv.unread_count || 0,
        lastMessage: conv.messages?.[0] ? {
          content: conv.messages[0].content,
          isFromCustomer: conv.messages[0].is_from_customer
        } : {
          content: '',
          isFromCustomer: false
        },
        aiContextSummary: conv.ai_context_summary,
        distributorId: conv.distributor_id,
        createdAt: conv.created_at,
        updatedAt: conv.updated_at
      }));

      console.log('loadConversations: Setting conversations', transformedConversations);
      setConversations(transformedConversations);
    } catch (error) {
      console.error('Error loading conversations:', error);
      setConversationsError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      console.log('loadConversations: Setting loading to false');
      setConversationsLoading(false);
    }
  }, [supabase, distributorId]);

  // Load messages for a specific conversation with RLS filtering
  const loadMessages = useCallback(async (convId: string) => {
    try {
      setMessagesLoading(true);
      setMessagesError(null);

      const { data, error } = await supabase
        .from('messages')
        .select(`
          id,
          conversation_id,
          content,
          is_from_customer,
          message_type,
          status,
          attachments,
          ai_processed,
          ai_confidence,
          ai_extracted_intent,
          ai_extracted_products,
          ai_suggested_responses,
          order_context_id,
          external_message_id,
          created_at,
          updated_at
        `)
        .eq('conversation_id', convId)
        .order('created_at', { ascending: true });

      if (error) {
        throw new Error(`Failed to load messages: ${(error as any)?.message || 'Unknown error'}`);
      }

      // Transform data to match frontend interface
      const transformedMessages: Message[] = (data || []).map((msg: any) => ({
        id: msg.id,
        conversationId: msg.conversation_id,
        content: msg.content,
        isFromCustomer: msg.is_from_customer,
        messageType: msg.message_type,
        status: msg.status,
        attachments: msg.attachments || [],
        aiProcessed: msg.ai_processed || false,
        aiConfidence: msg.ai_confidence,
        aiExtractedIntent: msg.ai_extracted_intent,
        aiExtractedProducts: msg.ai_extracted_products,
        aiSuggestedResponses: msg.ai_suggested_responses,
        orderContextId: msg.order_context_id,
        distributorId: distributorId, // Set from hook parameter since it's not in messages table
        externalMessageId: msg.external_message_id,
        createdAt: msg.created_at,
        updatedAt: msg.updated_at
      }));

      setMessages(transformedMessages);
    } catch (error) {
      console.error('Error loading messages:', error);
      setMessagesError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setMessagesLoading(false);
    }
  }, [supabase, distributorId]);

  // Send a new message
  const sendMessage = useCallback(async (data: SendMessageData) => {
    try {
      const messageData = {
        conversation_id: data.conversationId,
        content: data.content,
        is_from_customer: false,
        message_type: data.messageType || 'TEXT',
        status: 'SENT',
        attachments: data.attachments || [],
        ai_processed: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      const { data: newMessage, error } = await supabase
        .from('messages')
        .insert([messageData])
        .select()
        .single();

      if (error) {
        throw new Error(`Failed to send message: ${(error as any)?.message || 'Unknown error'}`);
      }

      // Optimistically update messages state
      if (newMessage && conversationId === data.conversationId) {
        const transformedMessage: Message = {
          id: newMessage.id,
          conversationId: newMessage.conversation_id,
          content: newMessage.content,
          isFromCustomer: newMessage.is_from_customer,
          messageType: newMessage.message_type,
          status: newMessage.status,
          attachments: newMessage.attachments || [],
          aiProcessed: newMessage.ai_processed || false,
          aiConfidence: newMessage.ai_confidence,
          aiExtractedIntent: newMessage.ai_extracted_intent,
          aiExtractedProducts: newMessage.ai_extracted_products,
          aiSuggestedResponses: newMessage.ai_suggested_responses,
          orderContextId: newMessage.order_context_id,
          distributorId: distributorId, // Set from hook parameter
          externalMessageId: newMessage.external_message_id,
          createdAt: newMessage.created_at,
          updatedAt: newMessage.updated_at
        };
        
        setMessages(prev => [...prev, transformedMessage]);
      }

      // Update conversation last_message_at
      await supabase
        .from('conversations')
        .update({ 
          last_message_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .eq('id', data.conversationId)
        .eq('distributor_id', distributorId);

      // Refresh conversations to update last message
      await loadConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }, [supabase, distributorId, conversationId, loadConversations]);

  // Mark messages as read
  const markAsRead = useCallback(async (messageIds: string[]) => {
    try {
      const { error } = await supabase
        .from('messages')
        .update({ 
          status: 'READ',
          updated_at: new Date().toISOString()
        })
        .in('id', messageIds);

      if (error) {
        throw new Error(`Failed to mark messages as read: ${(error as any)?.message || 'Unknown error'}`);
      }

      // Update local state
      setMessages(prev => prev.map(msg => 
        messageIds.includes(msg.id) ? { ...msg, status: 'READ' as const } : msg
      ));
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  }, [supabase]);

  // Create a new conversation
  const createConversation = useCallback(async (
    customerId: string, 
    channel: 'WHATSAPP' | 'SMS' | 'EMAIL'
  ): Promise<string> => {
    try {
      const conversationData = {
        customer_id: customerId,
        channel,
        status: 'ACTIVE',
        unread_count: 0,
        distributor_id: distributorId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_message_at: new Date().toISOString()
      };

      const { data, error } = await supabase
        .from('conversations')
        .insert([conversationData])
        .select()
        .single();

      if (error) {
        throw new Error(`Failed to create conversation: ${(error as any)?.message || 'Unknown error'}`);
      }

      await loadConversations();
      return data.id;
    } catch (error) {
      console.error('Error creating conversation:', error);
      throw error;
    }
  }, [supabase, distributorId, loadConversations]);

  // Archive a conversation
  const archiveConversation = useCallback(async (conversationId: string) => {
    try {
      const { error } = await supabase
        .from('conversations')
        .update({ 
          status: 'ARCHIVED',
          updated_at: new Date().toISOString()
        })
        .eq('id', conversationId)
        .eq('distributor_id', distributorId);

      if (error) {
        throw new Error(`Failed to archive conversation: ${(error as any)?.message || 'Unknown error'}`);
      }

      await loadConversations();
    } catch (error) {
      console.error('Error archiving conversation:', error);
      throw error;
    }
  }, [supabase, distributorId, loadConversations]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      loadMessages(conversationId);
    } else {
      setMessages([]);
    }
  }, [conversationId, loadMessages]);

  // Set up real-time subscriptions
  useEffect(() => {
    const conversationsSubscription = supabase
      .channel('conversations_changes')
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'conversations',
          filter: `distributor_id=eq.${distributorId}`
        }, 
        () => {
          loadConversations();
        }
      )
      .subscribe();

    const messagesSubscription = supabase
      .channel('messages_changes')
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'messages'
          // Note: RLS will handle filtering, no need for distributor_id filter
        }, 
        (payload: any) => {
          // Only refresh if it's for the current conversation
          if (payload.new && payload.new.conversation_id === conversationId && conversationId) {
            loadMessages(conversationId);
          }
          // Always refresh conversations to update last message
          loadConversations();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(conversationsSubscription);
      supabase.removeChannel(messagesSubscription);
    };
  }, [supabase, distributorId, conversationId, loadConversations, loadMessages]);

  return {
    conversations,
    conversationsLoading,
    conversationsError,
    messages,
    messagesLoading,
    messagesError,
    sendMessage,
    markAsRead,
    createConversation,
    archiveConversation,
    refreshConversations: loadConversations,
    refreshMessages: () => conversationId ? loadMessages(conversationId) : Promise.resolve()
  };
}