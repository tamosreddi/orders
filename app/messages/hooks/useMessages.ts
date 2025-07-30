'use client';

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../../../lib/supabase/client';
import { Conversation } from '../types/conversation';
import { Message, SendMessageData, MessageAttachment } from '../types/message';

/**
 * Gets the current distributor ID for the session
 * TODO: This should come from useAuth() hook when authentication is implemented
 */
function getCurrentDistributorId(): string {
  // Use the same development distributor ID from lib/api/customers.ts
  const DEV_DISTRIBUTOR_ID = '550e8400-e29b-41d4-a716-446655440000';
  return DEV_DISTRIBUTOR_ID;
}

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

export function useMessages({ distributorId, conversationId }: UseMessagesOptions): UseMessagesReturn {
  // Conversations state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [conversationsError, setConversationsError] = useState<string | null>(null);
  
  // Messages state
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  // Real-time messaging using Supabase Realtime (WebSocket-based)

  // Load conversations with RLS filtering
  const loadConversations = useCallback(async (isInitialLoad: boolean = false) => {
    try {
      if (isInitialLoad) {
        console.log('loadConversations: Initial load...');
        setConversationsLoading(true);
      }
      setConversationsError(null);

      // First get conversations
      const { data: conversationsData, error: conversationsError } = await supabase
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
          messages!conversations_last_message_id_fkey (
            content,
            is_from_customer
          )
        `)
        .eq('distributor_id', distributorId)
        .eq('status', 'ACTIVE')
        .order('last_message_at', { ascending: false });

      if (conversationsError) {
        throw new Error(`Failed to load conversations: ${conversationsError.message}`);
      }

      // Then get unread message counts for each conversation
      const conversationIds = conversationsData?.map(conv => conv.id) || [];
      let unreadCounts: Record<string, number> = {};
      
      if (conversationIds.length > 0) {
        const { data: messagesData, error: messagesError } = await supabase
          .from('messages')
          .select('conversation_id, id')
          .in('conversation_id', conversationIds)
          .eq('is_from_customer', true)
          .neq('status', 'READ');

        if (!messagesError && messagesData) {
          // Count unread messages per conversation
          messagesData.forEach(msg => {
            unreadCounts[msg.conversation_id] = (unreadCounts[msg.conversation_id] || 0) + 1;
          });
        }
      }

      const data = conversationsData;
      const error = conversationsError;

      if (error) {
        throw new Error(`Failed to load conversations: ${(error as any)?.message || 'Unknown error'}`);
      }

      // Transform data to match frontend interface
      const transformedConversations: Conversation[] = (data || []).map((conv: any) => {
        // Use the accurate unread count we calculated
        const actualUnreadCount = unreadCounts[conv.id] || 0;

        return {
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
          unreadCount: actualUnreadCount, // Use accurate calculated count
          lastMessage: conv.messages?.[0] ? {
            content: conv.messages[0].content || '',
            isFromCustomer: conv.messages[0].is_from_customer || false
          } : {
            content: '',
            isFromCustomer: false
          },
          aiContextSummary: conv.ai_context_summary,
          distributorId: conv.distributor_id,
          createdAt: conv.created_at,
          updatedAt: conv.updated_at
        };
      });

      // Only update state if data has actually changed
      setConversations(prev => {
        const hasChanged = JSON.stringify(prev) !== JSON.stringify(transformedConversations);
        if (hasChanged || isInitialLoad) {
          console.log('loadConversations: Data changed, updating state');
          return transformedConversations;
        }
        return prev;
      });
    } catch (error) {
      console.error('Error loading conversations:', error);
      setConversationsError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      if (isInitialLoad) {
        setConversationsLoading(false);
      }
    }
  }, [supabase, distributorId]);

  // Mark messages as read
  const markAsRead = useCallback(async (messageIds: string[]) => {
    try {
      const { error } = await supabase
        .from('messages')
        .update({ 
          status: 'READ' as const,
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
      
      // Trigger global unread count refresh for navigation
      window.dispatchEvent(new CustomEvent('refreshUnreadCount'));
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  }, [supabase]);

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
        attachments: (msg.attachments || []) as unknown as MessageAttachment[],
        aiProcessed: msg.ai_processed || false,
        aiConfidence: msg.ai_confidence ?? undefined,
        aiExtractedIntent: msg.ai_extracted_intent ?? undefined,
        aiExtractedProducts: (msg.ai_extracted_products as any[]) ?? undefined,
        aiSuggestedResponses: (msg.ai_suggested_responses as string[]) ?? undefined,
        orderContextId: msg.order_context_id ?? undefined,
        distributorId: distributorId, // Set from hook parameter since it's not in messages table
        externalMessageId: msg.external_message_id ?? undefined,
        createdAt: msg.created_at,
        updatedAt: msg.updated_at
      }));

      setMessages(transformedMessages);

      // Automatically mark unread customer messages as read when conversation is viewed
      const unreadCustomerMessages = transformedMessages.filter(
        msg => msg.isFromCustomer && msg.status !== 'READ'
      );

      if (unreadCustomerMessages.length > 0) {
        const messageIds = unreadCustomerMessages.map(msg => msg.id);
        await markAsRead(messageIds);
        
        // Reset unread count in conversation database
        const { error: updateError } = await supabase
          .from('conversations')
          .update({ 
            unread_count: 0,
            updated_at: new Date().toISOString()
          })
          .eq('id', convId)
          .eq('distributor_id', distributorId);

        if (updateError) {
          console.warn('Failed to update conversation unread_count:', updateError);
        }

        // Refresh conversations to update unread count in UI
        await loadConversations();
        
        // Trigger global unread count refresh for navigation
        window.dispatchEvent(new CustomEvent('refreshUnreadCount'));
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      setMessagesError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setMessagesLoading(false);
    }
  }, [supabase, distributorId, markAsRead, loadConversations]);

  // Send a new message
  const sendMessage = useCallback(async (data: SendMessageData) => {
    try {
      const messageData = {
        conversation_id: data.conversationId,
        content: data.content,
        is_from_customer: false,
        message_type: data.messageType || 'TEXT' as const,
        status: 'SENT' as const,
        attachments: (data.attachments || []) as any,
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
          attachments: (newMessage.attachments || []) as unknown as MessageAttachment[],
          aiProcessed: newMessage.ai_processed || false,
          aiConfidence: newMessage.ai_confidence ?? undefined,
          aiExtractedIntent: newMessage.ai_extracted_intent ?? undefined,
          aiExtractedProducts: (newMessage.ai_extracted_products as any[]) ?? undefined,
          aiSuggestedResponses: (newMessage.ai_suggested_responses as string[]) ?? undefined,
          orderContextId: newMessage.order_context_id ?? undefined,
          distributorId: distributorId, // Set from hook parameter
          externalMessageId: newMessage.external_message_id ?? undefined,
          createdAt: newMessage.created_at,
          updatedAt: newMessage.updated_at
        };
        
        setMessages(prev => [...prev, transformedMessage]);
      }

      // Update conversation last_message_at and last_message_id
      // For messages from customer, increment unread_count
      const updateData: any = {
        last_message_at: new Date().toISOString(),
        last_message_id: newMessage.id,
        updated_at: new Date().toISOString()
      };

      // Messages sent through sendMessage are always from distributor, not customer
      // So we don't increment unread_count here

      await supabase
        .from('conversations')
        .update(updateData)
        .eq('id', data.conversationId)
        .eq('distributor_id', distributorId);

      // Refresh conversations to update last message
      await loadConversations(); // Background update
      
      // Trigger global unread count refresh for navigation
      window.dispatchEvent(new CustomEvent('refreshUnreadCount'));
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }, [supabase, distributorId, conversationId, loadConversations]);


  // Create a new conversation
  const createConversation = useCallback(async (
    customerId: string, 
    channel: 'WHATSAPP' | 'SMS' | 'EMAIL'
  ): Promise<string> => {
    try {
      const conversationData = {
        customer_id: customerId,
        channel,
        status: 'ACTIVE' as const,
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

      await loadConversations(); // Background update
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
          status: 'ARCHIVED' as const,
          updated_at: new Date().toISOString()
        })
        .eq('id', conversationId)
        .eq('distributor_id', distributorId);

      if (error) {
        throw new Error(`Failed to archive conversation: ${(error as any)?.message || 'Unknown error'}`);
      }

      await loadConversations(); // Background update
    } catch (error) {
      console.error('Error archiving conversation:', error);
      throw error;
    }
  }, [supabase, distributorId, loadConversations]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations(true); // Initial load
  }, [loadConversations]);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      loadMessages(conversationId);
    } else {
      setMessages([]);
    }
  }, [conversationId, loadMessages]);

  // Real-time message updates via Supabase Realtime WebSocket

  // Set up real-time subscriptions for live updates
  useEffect(() => {
    
    // Set up messages subscription with better handling
    const messagesSubscription = supabase
      .channel(`messages_changes_${Date.now()}`) // Unique channel name
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'messages'
        }, 
        (payload: any) => {
          // Handle INSERT events (new messages)
          if (payload.eventType === 'INSERT' && payload.new) {
            // Always refresh conversations first to update last message and unread counts
            loadConversations();
            
            // If this message is for the currently selected conversation, add it immediately to the chat
            if (conversationId && payload.new.conversation_id === conversationId) {
              
              const newMessage: Message = {
                id: payload.new.id,
                conversationId: payload.new.conversation_id,
                content: payload.new.content,
                isFromCustomer: payload.new.is_from_customer,
                messageType: payload.new.message_type || 'TEXT',
                status: payload.new.status || 'DELIVERED',
                attachments: payload.new.attachments || [],
                aiProcessed: payload.new.ai_processed || false,
                aiConfidence: payload.new.ai_confidence,
                aiExtractedIntent: payload.new.ai_extracted_intent,
                aiExtractedProducts: payload.new.ai_extracted_products,
                aiSuggestedResponses: payload.new.ai_suggested_responses,
                orderContextId: payload.new.order_context_id,
                distributorId: distributorId,
                externalMessageId: payload.new.external_message_id,
                createdAt: payload.new.created_at,
                updatedAt: payload.new.updated_at
              };

              // Add message to current conversation chat immediately
              setMessages(prev => {
                // Check for duplicates
                const exists = prev.find(msg => msg.id === newMessage.id);
                if (exists) return prev;
                return [...prev, newMessage];
              });
            }
          }
          
          // Handle UPDATE events (message status changes, etc.)
          if (payload.eventType === 'UPDATE' && payload.new) {
            if (conversationId && payload.new.conversation_id === conversationId) {
              setMessages(prev => prev.map(msg => 
                msg.id === payload.new.id ? {
                  ...msg,
                  content: payload.new.content,
                  status: payload.new.status,
                  aiProcessed: payload.new.ai_processed,
                  updatedAt: payload.new.updated_at
                } : msg
              ));
            }
            loadConversations();
          }
        }
      )
      .subscribe((status) => {
        if (status !== 'SUBSCRIBED' && status !== 'CLOSED') {
          console.warn('Realtime connection issue:', status);
        }
      });

    // Set up conversations subscription
    const conversationsSubscription = supabase
      .channel(`conversations_changes_${Date.now()}`) // Unique channel name
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'conversations',
          filter: `distributor_id=eq.${distributorId}`
        }, 
        (payload) => {
          loadConversations();
        }
      )
      .subscribe((status) => {
        if (status !== 'SUBSCRIBED' && status !== 'CLOSED') {
          console.warn('Conversations realtime connection issue:', status);
        }
      });

    return () => {
      supabase.removeChannel(conversationsSubscription);
      supabase.removeChannel(messagesSubscription);
    };
  }, [distributorId, conversationId, loadConversations, loadMessages]);

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
    refreshConversations: () => loadConversations(),
    refreshMessages: () => conversationId ? loadMessages(conversationId) : Promise.resolve()
  };
}