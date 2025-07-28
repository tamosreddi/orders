'use client';

import { Search } from 'lucide-react';
import { Conversation } from '../types/conversation';

interface ChatListProps {
  conversations: Conversation[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  searchValue: string;
  onSearch: (value: string) => void;
}

export function ChatList({ 
  conversations, 
  selectedId, 
  onSelect, 
  searchValue, 
  onSearch 
}: ChatListProps) {
  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'WHATSAPP':
        return '💬';
      case 'SMS':
        return '📱';
      case 'EMAIL':
        return '📧';
      default:
        return '💬';
    }
  };

  const formatLastMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="w-80 bg-surface-0 text-text-primary h-full flex flex-col border-r border-border-subtle">
      {/* Header with Search */}
      <div className="p-4 border-b border-border-subtle">
        <h2 className="text-lg font-semibold text-text-primary mb-3">CHATS</h2>
        
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted h-4 w-4" />
          <input
            type="text"
            placeholder="Search..."
            value={searchValue}
            onChange={(e) => onSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-surface-1 text-text-primary placeholder-text-muted rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all duration-fast"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center">
            <div className="text-text-muted text-sm">
              {searchValue ? 'No conversations found' : 'No conversations yet'}
            </div>
            <div className="text-text-muted text-xs mt-1">
              {searchValue ? 'Try a different search term' : 'Start messaging your customers'}
            </div>
          </div>
        ) : (
          conversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => onSelect(conversation.id)}
              className={`p-4 border-b border-border-subtle cursor-pointer transition-colors duration-fast ${
                selectedId === conversation.id 
                  ? 'bg-blue-50 border-l-4 border-l-blue-500' 
                  : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-start space-x-3">
                {/* Customer Avatar */}
                <div className="w-10 h-10 bg-primary-500 rounded-full flex-shrink-0 flex items-center justify-center">
                  {conversation.customer.avatar ? (
                    <img
                      src={conversation.customer.avatar}
                      alt={conversation.customer.name}
                      className="w-full h-full rounded-full object-cover"
                    />
                  ) : (
                    <span className="text-white text-sm font-medium">
                      {conversation.customer.name.charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>

                {/* Conversation Details */}
                <div className="flex-1 min-w-0">
                  {/* Name and Unread Badge */}
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-text-primary truncate">
                      {conversation.customer.name}
                    </p>
                    {conversation.unreadCount > 0 && (
                      <span className="bg-state-success text-white text-xs px-2 py-1 rounded-full font-medium min-w-5 text-center">
                        {conversation.unreadCount}
                      </span>
                    )}
                  </div>

                  {/* Last Message */}
                  <p className="text-xs text-text-muted truncate mb-2">
                    {conversation.lastMessage.isFromCustomer ? '' : 'You: '}
                    {conversation.lastMessage.content}
                  </p>

                  {/* Channel and Time */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1">
                      <span className="text-xs">
                        {getChannelIcon(conversation.channel)}
                      </span>
                      <span className="text-xs text-text-muted uppercase">
                        {conversation.channel}
                      </span>
                    </div>
                    <span className="text-xs text-text-muted">
                      {formatLastMessageTime(conversation.lastMessageAt)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer with Status */}
      <div className="p-4 border-t border-border-subtle">
        <div className="flex items-center justify-center text-xs text-text-muted">
          <span>{conversations.length} conversation{conversations.length !== 1 ? 's' : ''}</span>
        </div>
      </div>
    </div>
  );
}