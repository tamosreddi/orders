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
    <div className="w-80 bg-brand-navy-900 text-white h-full flex flex-col">
      {/* Header with Search */}
      <div className="p-4 border-b border-brand-navy-700">
        <h2 className="text-lg font-semibold text-white mb-3">Messages</h2>
        
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-300 h-4 w-4" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchValue}
            onChange={(e) => onSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-brand-navy-700 text-white placeholder-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-fast"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center">
            <div className="text-gray-300 text-sm">
              {searchValue ? 'No conversations found' : 'No conversations yet'}
            </div>
            <div className="text-gray-400 text-xs mt-1">
              {searchValue ? 'Try a different search term' : 'Start messaging your customers'}
            </div>
          </div>
        ) : (
          conversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => onSelect(conversation.id)}
              className={`p-4 border-b border-brand-navy-700 cursor-pointer hover:bg-brand-navy-700 transition-colors duration-fast ${
                selectedId === conversation.id ? 'bg-brand-navy-700' : ''
              }`}
            >
              <div className="flex items-start space-x-3">
                {/* Customer Avatar */}
                <div className="w-10 h-10 bg-gray-300 rounded-full flex-shrink-0 flex items-center justify-center">
                  {conversation.customer.avatar ? (
                    <img
                      src={conversation.customer.avatar}
                      alt={conversation.customer.name}
                      className="w-full h-full rounded-full object-cover"
                    />
                  ) : (
                    <span className="text-gray-600 text-sm font-medium">
                      {conversation.customer.name.charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>

                {/* Conversation Details */}
                <div className="flex-1 min-w-0">
                  {/* Name and Unread Badge */}
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-white truncate">
                      {conversation.customer.name}
                    </p>
                    {conversation.unreadCount > 0 && (
                      <span className="bg-state-success text-white text-xs px-2 py-1 rounded-full font-medium min-w-5 text-center">
                        {conversation.unreadCount}
                      </span>
                    )}
                  </div>

                  {/* Last Message */}
                  <p className="text-xs text-gray-300 truncate mb-2">
                    {conversation.lastMessage.isFromCustomer ? '' : 'You: '}
                    {conversation.lastMessage.content}
                  </p>

                  {/* Channel and Time */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1">
                      <span className="text-xs">
                        {getChannelIcon(conversation.channel)}
                      </span>
                      <span className="text-xs text-gray-400 uppercase">
                        {conversation.channel}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
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
      <div className="p-4 border-t border-brand-navy-700">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>{conversations.length} conversation{conversations.length !== 1 ? 's' : ''}</span>
          <span className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-state-success rounded-full"></div>
            <span>Online</span>
          </span>
        </div>
      </div>
    </div>
  );
}