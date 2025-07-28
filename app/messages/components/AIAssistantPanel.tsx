'use client';

import { useState } from 'react';
import { Bot, User, ShoppingCart, TrendingUp, Star, Clock, ArrowRight } from 'lucide-react';
import { Conversation } from '../types/conversation';
import { Message } from '../types/message';

interface AIAssistantPanelProps {
  conversationId: string | null;
  conversation: Conversation | null;
  messages: Message[];
  onSendSuggestion?: (suggestion: string) => void;
  onCreateOrder?: () => void;
  onViewCustomerOrders?: () => void;
}

export function AIAssistantPanel({ 
  conversationId, 
  conversation,
  messages,
  onSendSuggestion,
  onCreateOrder,
  onViewCustomerOrders
}: AIAssistantPanelProps) {
  const [isProcessing, setIsProcessing] = useState(false);

  if (!conversationId || !conversation) {
    return (
      <div className="w-80 border-l border-border-subtle bg-surface-0 p-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-surface-alt rounded-full mx-auto flex items-center justify-center mb-4">
            <Bot className="w-8 h-8 text-text-muted" />
          </div>
          <h3 className="text-lg font-semibold text-text-default mb-2">AI Assistant</h3>
          <p className="text-sm text-text-muted">
            Select a conversation to see AI-powered suggestions and insights
          </p>
        </div>
      </div>
    );
  }

  // Mock AI suggestions based on conversation context
  const getAISuggestions = () => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return [];

    const content = lastMessage.content.toLowerCase();
    
    if (content.includes('order') || content.includes('need') || content.includes('want')) {
      return [
        "I'd be happy to help you with your order. What products are you looking for?",
        "Let me check our available products for you.",
        "Would you like me to create an order for your usual items?"
      ];
    } else if (content.includes('delivery') || content.includes('when')) {
      return [
        "Our standard delivery time is 24-48 hours.",
        "Let me check the delivery schedule for your area.",
        "Would you like to track your current orders?"
      ];
    } else if (content.includes('thank') || content.includes('thanks')) {
      return [
        "You're very welcome! Is there anything else I can help you with?",
        "Happy to help! Have a great day!",
        "Thank you for your business!"
      ];
    } else {
      return [
        "Thank you for your message. How can I assist you today?",
        "I'm here to help with any questions about our products or orders.",
        "Would you like to see our latest product catalog?"
      ];
    }
  };

  const suggestions = getAISuggestions();

  // Mock customer insights
  const getCustomerInsights = () => {
    return {
      totalOrders: 15,
      averageOrderValue: 250,
      lastOrderDate: '2024-01-10',
      preferredProducts: ['Fresh Vegetables', 'Dairy Products'],
      riskLevel: 'Low',
      loyaltyScore: 85
    };
  };

  const customerInsights = getCustomerInsights();

  // Mock order detection from recent messages
  const detectPotentialOrders = () => {
    const recentMessages = messages.slice(-3);
    const hasOrderKeywords = recentMessages.some(msg => 
      msg.content.toLowerCase().includes('order') ||
      msg.content.toLowerCase().includes('need') ||
      msg.content.toLowerCase().includes('want') ||
      msg.content.toLowerCase().includes('kg') ||
      msg.content.toLowerCase().includes('boxes')
    );
    
    return hasOrderKeywords;
  };

  const hasPotentialOrder = detectPotentialOrders();

  return (
    <div className="w-80 border-l border-border-subtle bg-surface-0 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border-subtle">
        <div className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-brand-navy-900" />
          <h3 className="text-lg font-semibold text-text-default">AI Assistant</h3>
          {isProcessing && (
            <div className="w-2 h-2 bg-brand-navy-900 rounded-full animate-pulse"></div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Status Indicator */}
        <div className="p-4 border-b border-border-subtle">
          <div className="flex items-center justify-center">
            <span className="inline-flex items-center px-4 py-2 text-sm font-medium bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">
              <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full mr-2 animate-pulse"></div>
              Currently Active
            </span>
          </div>
        </div>

        {/* Customer Insights */}
        <div className="p-4 border-b border-border-subtle">
          <h4 className="text-sm font-medium text-text-default mb-3 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2" />
            Customer Insights
          </h4>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-surface-alt rounded p-2 text-center">
                <div className="font-semibold text-text-default">{customerInsights.totalOrders}</div>
                <div className="text-text-muted">Total Orders</div>
              </div>
              <div className="bg-surface-alt rounded p-2 text-center">
                <div className="font-semibold text-text-default">${customerInsights.averageOrderValue}</div>
                <div className="text-text-muted">Avg. Value</div>
              </div>
            </div>
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-text-muted">Last Order:</span>
                <span className="text-text-default">{customerInsights.lastOrderDate}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Risk Level:</span>
                <span className="text-state-success">{customerInsights.riskLevel}</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-text-muted mb-1">Preferred Products:</div>
              <div className="flex flex-wrap gap-1">
                {customerInsights.preferredProducts.map((product, index) => (
                  <span 
                    key={index}
                    className="text-xs px-2 py-1 bg-brand-navy-50 text-brand-navy-900 rounded"
                  >
                    {product}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Order Detection Alert */}
        {hasPotentialOrder && (
          <div className="p-4 border-b border-border-subtle">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-start space-x-2">
                <Bot className="w-4 h-4 text-blue-600 mt-0.5" />
                <div className="flex-1">
                  <h5 className="text-sm font-medium text-blue-900 mb-1">
                    Order Detected
                  </h5>
                  <p className="text-xs text-blue-700 mb-2">
                    AI detected potential order request in the conversation
                  </p>
                  <button
                    onClick={onCreateOrder}
                    className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
                  >
                    Create Order
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Suggestions */}
        <div className="p-4 border-b border-border-subtle">
          <h4 className="text-sm font-medium text-text-default mb-3 flex items-center">
            <Bot className="w-4 h-4 mr-2" />
            Suggested Responses
          </h4>
          {suggestions.length === 0 ? (
            <div className="text-xs text-text-muted text-center py-2">
              No suggestions available
            </div>
          ) : (
            <div className="space-y-2">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => onSendSuggestion?.(suggestion)}
                  className="w-full text-left p-2 bg-surface-alt rounded-lg text-xs hover:bg-border-subtle transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <span className="flex-1 pr-2">{suggestion}</span>
                    <ArrowRight className="w-3 h-3 text-text-muted group-hover:text-text-default transition-colors" />
                  </div>
                </button>
              ))}
            </div>
          )}
          
          <div className="mt-3 pt-3 border-t border-border-subtle">
            <button 
              className="w-full text-xs text-brand-navy-900 hover:text-brand-navy-700 transition-colors"
              onClick={() => setIsProcessing(true)}
            >
              Generate Custom Response
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="p-4">
          <h4 className="text-sm font-medium text-text-default mb-3 flex items-center">
            <Clock className="w-4 h-4 mr-2" />
            Quick Actions
          </h4>
          <div className="space-y-2">
            <button
              onClick={onCreateOrder}
              className="w-full py-2 px-3 bg-state-success text-white rounded-lg text-sm hover:opacity-90 transition-opacity flex items-center justify-center space-x-2"
            >
              <ShoppingCart className="w-4 h-4" />
              <span>Create Order</span>
            </button>
            <button
              onClick={onViewCustomerOrders}
              className="w-full py-2 px-3 border border-border-subtle rounded-lg text-sm hover:bg-surface-alt transition-colors flex items-center justify-center space-x-2"
            >
              <TrendingUp className="w-4 h-4" />
              <span>View Order History</span>
            </button>
            <button className="w-full py-2 px-3 border border-border-subtle rounded-lg text-sm hover:bg-surface-alt transition-colors">
              Send Product Catalog
            </button>
            <button className="w-full py-2 px-3 border border-border-subtle rounded-lg text-sm hover:bg-surface-alt transition-colors">
              Schedule Follow-up
            </button>
          </div>
        </div>
      </div>

      {/* AI Status Footer */}
      <div className="p-4 border-t border-border-subtle">
        <div className="flex items-center justify-between text-xs text-text-muted">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-state-success rounded-full"></div>
            <span>AI Active</span>
          </div>
          <span>Confidence: 85%</span>
        </div>
      </div>
    </div>
  );
}