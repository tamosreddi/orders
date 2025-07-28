'use client';

import { useState, useMemo, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Conversation } from './types/conversation';
import { Message } from './types/message';

// Import actual components
import { ChatList } from './components/ChatList';
import { MessageThread } from './components/MessageThread';
import { AIAssistantPanel } from './components/AIAssistantPanel';

// Import hooks
import { useMessages } from './hooks/useMessages';
import { useAIAgent } from './hooks/useAIAgent';

export default function MessagesPage() {
  const router = useRouter();
  
  // State management
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [searchValue, setSearchValue] = useState('');
  
  // TODO: Get distributor ID from auth context or session
  const distributorId = process.env.NEXT_PUBLIC_DEMO_DISTRIBUTOR_ID || '550e8400-e29b-41d4-a716-446655440000';

  // Use hooks for data management
  const {
    conversations,
    conversationsLoading,
    conversationsError,
    messages,
    messagesLoading,
    messagesError,
    sendMessage,
    markAsRead,
    createConversation,
    archiveConversation
  } = useMessages({ distributorId, conversationId: selectedConversation });

  const {
    isProcessing: aiProcessing,
    lastError: aiError,
    processMessage,
    extractOrderFromMessage,
    generateResponseSuggestions,
    analyzeCustomerConversation,
    detectOrderIntent
  } = useAIAgent({ distributorId });

  // Auto-select the most recent conversation when conversations are loaded
  useEffect(() => {
    if (conversations.length > 0 && !selectedConversation && !searchValue) {
      // Find the most recent conversation (sorted by lastMessageAt)
      const mostRecentConversation = conversations.reduce((latest, current) => 
        new Date(current.lastMessageAt) > new Date(latest.lastMessageAt) ? current : latest
      );
      setSelectedConversation(mostRecentConversation.id);
    }
  }, [conversations, selectedConversation, searchValue]);

  // Filter conversations based on search
  const filteredConversations = useMemo(() => {
    if (!searchValue.trim()) return conversations;
    
    const searchTerm = searchValue.toLowerCase();
    return conversations.filter(conversation =>
      conversation.customer.name.toLowerCase().includes(searchTerm) ||
      conversation.customer.code.toLowerCase().includes(searchTerm) ||
      conversation.lastMessage.content.toLowerCase().includes(searchTerm)
    );
  }, [conversations, searchValue]);

  // Get selected conversation object
  const selectedConversationObj = useMemo(() => {
    return selectedConversation 
      ? conversations.find(c => c.id === selectedConversation) || null
      : null;
  }, [selectedConversation, conversations]);

  // Handle sending a message
  const handleSendMessage = async (content: string) => {
    if (!selectedConversation) return;

    try {
      await sendMessage({
        conversationId: selectedConversation,
        content,
        messageType: 'TEXT'
      });

      // Process message with AI in background
      if (detectOrderIntent(content)) {
        try {
          const orderResult = await extractOrderFromMessage(content);
          if (orderResult.extractedProducts.length > 0) {
            console.log('Order detected:', orderResult);
            // TODO: Show order creation prompt
          }
        } catch (error) {
          console.warn('AI order processing failed:', error);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // Handle AI suggestion selection
  const handleSendSuggestion = async (suggestion: string) => {
    if (selectedConversation) {
      await handleSendMessage(suggestion);
    }
  };

  // Handle order creation from AI
  const handleCreateOrder = () => {
    if (selectedConversationObj) {
      router.push(`/orders/create?conversation=${selectedConversation}&customer=${selectedConversationObj.customerId}`);
    }
  };

  // Handle viewing customer orders
  const handleViewCustomerOrders = () => {
    if (selectedConversationObj) {
      router.push(`/orders?customer=${selectedConversationObj.customerId}`);
    }
  };

  if (conversationsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-text-muted">Loading messages...</div>
      </div>
    );
  }

  if (conversationsError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-state-error mb-2">Error loading conversations</div>
          <div className="text-text-muted text-sm">{conversationsError}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-surface-0 flex flex-col">
      {/* Page Header */}
      <div className="px-6 py-4 border-b border-border-subtle">
        <h1 className="text-heading-xl font-sans text-primary-ink font-antialiased">
          MENSAJES
        </h1>
      </div>

      {/* Three-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chat List */}
        <ChatList 
          conversations={filteredConversations}
          selectedId={selectedConversation}
          onSelect={setSelectedConversation}
          searchValue={searchValue}
          onSearch={setSearchValue}
        />
        
        {/* Center Panel - Message Thread */}
        <MessageThread
          conversationId={selectedConversation}
          conversation={selectedConversationObj}
          messages={messages}
          onSendMessage={handleSendMessage}
          isTyping={aiProcessing}
        />
        
        {/* Right Panel - AI Assistant */}
        <AIAssistantPanel
          conversationId={selectedConversation}
          conversation={selectedConversationObj}
          messages={messages}
          onSendSuggestion={handleSendSuggestion}
          onCreateOrder={handleCreateOrder}
          onViewCustomerOrders={handleViewCustomerOrders}
        />
      </div>
    </div>
  );
}