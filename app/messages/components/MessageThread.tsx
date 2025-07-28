'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Smile } from 'lucide-react';
import { Message } from '../types/message';
import { Conversation } from '../types/conversation';

interface MessageThreadProps {
  conversationId: string | null;
  conversation?: Conversation | null;
  messages: Message[];
  onSendMessage: (content: string) => void;
  isTyping?: boolean;
}

export function MessageThread({ 
  conversationId, 
  conversation,
  messages, 
  onSendMessage,
  isTyping = false
}: MessageThreadProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  const handleSend = () => {
    const content = inputValue.trim();
    if (content) {
      onSendMessage(content);
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
      });
    }
  };

  const getMessageStatusIcon = (status: string) => {
    switch (status) {
      case 'SENT':
        return '✓';
      case 'DELIVERED':
        return '✓✓';
      case 'READ':
        return '✓✓';
      default:
        return '';
    }
  };

  if (!conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-surface-0">
        <div className="text-center text-text-muted max-w-md">
          <div className="mb-4">
            <div className="w-16 h-16 bg-surface-alt rounded-full mx-auto flex items-center justify-center">
              <Send className="w-8 h-8 text-text-muted" />
            </div>
          </div>
          <h3 className="text-lg font-medium mb-2 text-text-default">Welcome to Messages</h3>
          <p className="text-sm">
            Select a conversation from the sidebar to start messaging with your customers
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-surface-0">
      {/* Conversation Header */}
      {conversation && (
        <div className="px-6 py-4 border-b border-border-subtle">
          <div className="flex items-center space-x-3">
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
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-text-default">
                {conversation.customer.name}
              </h3>
              <div className="flex items-center space-x-2 text-sm text-text-muted">
                {conversation.channel === 'WHATSAPP' && (
                  <>
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      WhatsApp
                    </span>
                    {/* Show phone number for WhatsApp customers */}
                    {conversation.customer.name.includes('+') && (
                      <span className="text-xs text-text-muted font-mono">
                        {conversation.customer.name.match(/\+\d+/)?.[0]}
                      </span>
                    )}
                  </>
                )}
                {conversation.channel === 'SMS' && (
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    SMS
                  </span>
                )}
                {conversation.channel === 'EMAIL' && (
                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                    Email
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Message History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-text-muted py-8">
            <p className="text-sm">No messages yet</p>
            <p className="text-xs mt-1">Start the conversation below</p>
          </div>
        ) : (
          <>
            {messages.map((message, index) => {
              const isLastMessage = index === messages.length - 1;
              const isSameAuthorAsPrevious = 
                index > 0 && messages[index - 1].isFromCustomer === message.isFromCustomer;
              
              return (
                <div
                  key={message.id}
                  className={`flex ${message.isFromCustomer ? 'justify-start' : 'justify-end'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                      message.isFromCustomer
                        ? 'bg-surface-alt text-text-default'
                        : 'bg-brand-navy-900 text-white'
                    } ${
                      isSameAuthorAsPrevious 
                        ? 'mt-1' 
                        : 'mt-4'
                    }`}
                  >
                    {/* Message Content */}
                    <p className="text-sm whitespace-pre-wrap break-words">
                      {message.content}
                    </p>
                    
                    {/* Message Meta */}
                    <div className={`flex items-center justify-between mt-2 text-xs ${
                      message.isFromCustomer ? 'text-text-muted' : 'text-white/70'
                    }`}>
                      <span>{formatMessageTime(message.createdAt)}</span>
                      {!message.isFromCustomer && (
                        <span className="ml-2">
                          {getMessageStatusIcon(message.status)}
                        </span>
                      )}
                    </div>
                    
                    {/* AI Processing Indicator */}
                    {message.aiProcessed && message.aiConfidence && (
                      <div className="mt-2 text-xs opacity-75">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                          AI: {Math.round(message.aiConfidence * 100)}%
                        </span>
                      </div>
                    )}
                    
                    
                    {/* AI Extracted Intent Display */}
                    {message.aiExtractedIntent && (
                      <div className="mt-2 text-xs opacity-75">
                        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">
                          Intent: {message.aiExtractedIntent}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-surface-alt px-4 py-3 rounded-lg max-w-xs">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-text-muted rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-text-muted rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-text-muted rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Message Input */}
      <div className="border-t border-border-subtle p-4">
        <div className="flex items-end space-x-3">
          {/* Attachment Button */}
          <button className="p-2 text-text-muted hover:text-text-default transition-colors">
            <Paperclip className="w-5 h-5" />
          </button>
          
          {/* Message Input */}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              rows={1}
              className="w-full px-4 py-3 pr-12 border border-border-subtle rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-brand-navy-900 focus:border-transparent transition-all duration-fast"
              style={{ minHeight: '48px' }}
            />
            
            {/* Emoji Button */}
            <button className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-text-muted hover:text-text-default transition-colors">
              <Smile className="w-4 h-4" />
            </button>
          </div>
          
          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="p-3 bg-brand-navy-900 text-white rounded-lg hover:bg-brand-navy-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-fast"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        {/* Input Helper Text */}
        <div className="mt-2 text-xs text-text-muted">
          Press Enter to send, Shift + Enter for new line
        </div>
      </div>
    </div>
  );
}