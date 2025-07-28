'use client';

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabase/client';

/**
 * Gets the current distributor ID for the session
 * TODO: This should come from useAuth() hook when authentication is implemented
 */
function getCurrentDistributorId(): string {
  // Use the same development distributor ID from messages hook
  const DEV_DISTRIBUTOR_ID = '550e8400-e29b-41d4-a716-446655440000';
  return DEV_DISTRIBUTOR_ID;
}

interface UseHasUnreadMessagesReturn {
  hasUnreadMessages: boolean;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Lightweight hook to check if user has any unread messages across all conversations
 * Uses a simple EXISTS query for minimal performance impact
 */
export function useHasUnreadMessages(): UseHasUnreadMessagesReturn {
  const [hasUnreadMessages, setHasUnreadMessages] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const distributorId = getCurrentDistributorId();

  // Check for unread messages with lightweight query
  const checkUnreadMessages = useCallback(async () => {
    try {
      setError(null);

      // Use a more reliable approach - get all conversations and check for unread count
      const { data, error } = await supabase
        .from('conversations')
        .select('id, unread_count')
        .eq('distributor_id', distributorId)
        .eq('status', 'ACTIVE');

      if (error) {
        throw new Error(`Failed to check unread messages: ${error.message}`);
      }

      // Check if any conversation has unread messages
      const hasUnread = (data || []).some(conv => conv.unread_count > 0);
      console.log('useHasUnreadMessages - conversations data:', data);
      console.log('useHasUnreadMessages - hasUnread result:', hasUnread);
      setHasUnreadMessages(hasUnread);
    } catch (error) {
      console.error('Error checking unread messages:', error);
      setError(error instanceof Error ? error.message : 'Unknown error');
      setHasUnreadMessages(false); // Default to false on error
    } finally {
      setLoading(false);
    }
  }, [distributorId]);

  // Initial load
  useEffect(() => {
    checkUnreadMessages();
  }, [checkUnreadMessages]);

  // Listen for custom refresh events (e.g., when messages are read)
  useEffect(() => {
    const handleRefreshUnreadCount = () => {
      console.log('Received refresh unread count event');
      checkUnreadMessages();
    };

    window.addEventListener('refreshUnreadCount', handleRefreshUnreadCount);
    
    return () => {
      window.removeEventListener('refreshUnreadCount', handleRefreshUnreadCount);
    };
  }, [checkUnreadMessages]);

  // Set up lightweight real-time subscription for conversation changes
  useEffect(() => {
    console.log('Setting up unread messages subscription...');
    
    const conversationsSubscription = supabase
      .channel('unread_messages_check')
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'conversations',
          filter: `distributor_id=eq.${distributorId}`
        }, 
        (payload) => {
          console.log('Conversation change detected for unread check:', payload);
          // Refresh on any conversation change that might affect unread count
          checkUnreadMessages();
        }
      )
      .subscribe();

    // Also listen to message changes as they can affect unread counts
    const messagesSubscription = supabase
      .channel('messages_unread_check')
      .on('postgres_changes', 
        { 
          event: '*', 
          schema: 'public', 
          table: 'messages'
        }, 
        (payload) => {
          console.log('Message change detected for unread check:', payload);
          // Refresh when messages are inserted, updated (read status), or deleted
          checkUnreadMessages();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(conversationsSubscription);
      supabase.removeChannel(messagesSubscription);
    };
  }, [distributorId, checkUnreadMessages]);

  return {
    hasUnreadMessages,
    loading,
    error,
    refresh: checkUnreadMessages
  };
}