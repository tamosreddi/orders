'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Bot, User, ShoppingCart, TrendingUp, Star, Clock, ArrowRight, Package, AlertCircle, CheckCircle } from 'lucide-react';
import { Conversation } from '../types/conversation';
import { Message } from '../types/message';
import { useCustomerOrders } from '@/lib/hooks/useCustomerOrders';

// Order session types
interface OrderSessionItem {
  id: string;
  product_name: string;
  quantity: number;
  product_unit: string;
  ai_confidence: number;
  original_text: string;
}

interface OrderSession {
  id: string;
  status: 'ACTIVE' | 'COLLECTING' | 'REVIEWING' | 'CLOSED';
  started_at: string;
  last_activity_at: string;
  expires_at: string;
  total_messages_count: number;
  confidence_score: number;
  items?: OrderSessionItem[];
}

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
  const [activeSession, setActiveSession] = useState<OrderSession | null>(null);
  const [sessionLoading, setSessionLoading] = useState(false);
  const router = useRouter();
  
  // Fetch real customer order statistics
  const { orderStats, loading: orderStatsLoading } = useCustomerOrders(conversation?.customerId || null);

  // Fetch active order session for this conversation
  useEffect(() => {
    if (!conversationId) return;

    // DISABLED: Order sessions feature not active yet
    // Remove this to clean up logs until migration is applied
    setSessionLoading(false);
    setActiveSession(null);
    
    // TODO: Re-enable when order sessions migration is applied
    /*
    const fetchActiveSession = async () => {
      setSessionLoading(true);
      try {
        const response = await fetch(`/api/order-sessions/active?conversationId=${conversationId}`);
        
        if (response.ok) {
          const sessionData = await response.json();
          setActiveSession(sessionData);
        } else {
          setActiveSession(null);
        }
      } catch (error) {
        console.error('Failed to fetch active session:', error);
        setActiveSession(null);
      } finally {
        setSessionLoading(false);
      }
    };

    fetchActiveSession();
    
    // Poll for session updates every 10 seconds
    const interval = setInterval(fetchActiveSession, 10000);
    
    return () => clearInterval(interval);
    */
  }, [conversationId]);

  // Handle session actions
  const handleCloseSession = async () => {
    if (!activeSession) return;
    
    try {
      setIsProcessing(true);
      const response = await fetch(`/api/order-sessions/${activeSession.id}/close`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.order_created) {
          // Session closed and order created successfully
          setActiveSession(null);
          // Optionally redirect to order review
          if (result.order_id) {
            router.push(`/orders/${result.order_id}/review`);
          }
        }
      }
    } catch (error) {
      console.error('Failed to close session:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancelSession = async () => {
    if (!activeSession) return;
    
    try {
      setIsProcessing(true);
      const response = await fetch(`/api/order-sessions/${activeSession.id}/cancel`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setActiveSession(null);
      }
    } catch (error) {
      console.error('Failed to cancel session:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!conversationId || !conversation) {
    return (
      <div className="w-80 border-l border-border-subtle bg-surface-0 p-6">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto flex items-center justify-center mb-4">
            <Image
              src="/logos/bot.png"
              alt="AI Assistant Bot"
              width={64}
              height={64}
              className="w-16 h-16 object-contain"
            />
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

  // Get real customer insights from order statistics
  const getCustomerInsights = () => {
    if (!orderStats) {
      return {
        totalOrders: 0,
        averageOrderValue: 0,
        lastOrderDate: null,
        preferredProducts: [],
        riskLevel: 'Unknown'
      };
    }

    // Determine risk level based on order history
    const getRiskLevel = () => {
      if (orderStats.totalOrders === 0) return 'New Customer';
      if (orderStats.totalOrders >= 10) return 'Low';
      if (orderStats.totalOrders >= 5) return 'Medium';
      return 'High';
    };

    return {
      totalOrders: orderStats.totalOrders,
      averageOrderValue: orderStats.averageOrderValue,
      lastOrderDate: orderStats.lastOrderedDate,
      preferredProducts: [], // TODO: Could be enhanced with product analysis
      riskLevel: getRiskLevel()
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

  // Handle View Order History button click
  const handleViewOrderHistory = () => {
    if (!orderStats || orderStats.totalOrders === 0) {
      // Simple alert for no orders
      alert('This customer has no orders yet.');
      return;
    }
    
    // Redirect with customer filter
    router.push(`/orders?customer=${conversation?.customer.code}`);
  };

  return (
    <div className="w-80 border-l border-border-subtle bg-surface-0 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border-subtle">
        <div className="flex items-center space-x-2">
          <Image
            src="/logos/bot.png"
            alt="AI Assistant Bot"
            width={20}
            height={20}
            className="w-5 h-5 object-contain"
          />
          <h3 className="text-lg font-semibold text-text-default">AI Assistant</h3>
          {isProcessing && (
            <div className="w-2 h-2 bg-brand-navy-900 rounded-full animate-pulse"></div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Status Indicator - Hidden for now */}
        {/*
        <div className="p-4 border-b border-border-subtle">
          <div className="flex items-center justify-center">
            <span className="inline-flex items-center px-4 py-2 text-sm font-medium bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">
              <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full mr-2 animate-pulse"></div>
              Currently Active
            </span>
          </div>
        </div>
        */}

        {/* Active Order Session */}
        {sessionLoading ? (
          <div className="p-4 border-b border-border-subtle">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-300 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>
        ) : activeSession ? (
          <div className="p-4 border-b border-border-subtle">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Package className="w-4 h-4 text-blue-600" />
                  <h5 className="text-sm font-medium text-blue-900">
                    Active Order Session
                  </h5>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  activeSession.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                  activeSession.status === 'COLLECTING' ? 'bg-blue-100 text-blue-800' :
                  activeSession.status === 'REVIEWING' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {activeSession.status}
                </span>
              </div>
              
              <div className="text-xs text-blue-700 mb-3 space-y-1">
                <div className="flex justify-between">
                  <span>Messages:</span>
                  <span className="font-medium">{activeSession.total_messages_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Started:</span>
                  <span className="font-medium">
                    {new Date(activeSession.started_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Confidence:</span>
                  <span className={`font-medium ${
                    activeSession.confidence_score >= 0.8 ? 'text-green-600' :
                    activeSession.confidence_score >= 0.6 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {Math.round(activeSession.confidence_score * 100)}%
                  </span>
                </div>
              </div>

              {/* Session Items */}
              {activeSession.items && activeSession.items.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs text-blue-800 font-medium mb-2">
                    Collected Items ({activeSession.items.length}):
                  </div>
                  <div className="space-y-1 max-h-24 overflow-y-auto">
                    {activeSession.items.map((item) => (
                      <div key={item.id} className="bg-white rounded px-2 py-1 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-gray-900">
                            {item.quantity} {item.product_unit} {item.product_name}
                          </span>
                          <span className={`text-xs ${
                            item.ai_confidence >= 0.8 ? 'text-green-600' :
                            item.ai_confidence >= 0.6 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {Math.round(item.ai_confidence * 100)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Session Actions */}
              <div className="flex space-x-2">
                <button
                  onClick={handleCloseSession}
                  disabled={isProcessing || activeSession.status === 'REVIEWING'}
                  className="flex-1 text-xs bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-1"
                >
                  <CheckCircle className="w-3 h-3" />
                  <span>Complete Order</span>
                </button>
                <button
                  onClick={handleCancelSession}
                  disabled={isProcessing}
                  className="text-xs border border-blue-300 text-blue-700 px-3 py-2 rounded hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  <AlertCircle className="w-3 h-3" />
                </button>
              </div>

              {/* Expiry Warning */}
              {new Date(activeSession.expires_at) <= new Date(Date.now() + 5 * 60 * 1000) && (
                <div className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                  ⚠️ Session expires in {Math.round((new Date(activeSession.expires_at).getTime() - Date.now()) / 60000)} minutes
                </div>
              )}
            </div>
          </div>
        ) : null}

        {/* Customer Insights */}
        <div className="p-4 border-b border-border-subtle">
          <h4 className="text-sm font-medium text-text-default mb-3 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2" />
            Customer Insights
          </h4>
          {orderStatsLoading ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-surface-alt rounded p-2 text-center animate-pulse">
                  <div className="h-4 bg-gray-300 rounded mb-1"></div>
                  <div className="text-text-muted">Total Orders</div>
                </div>
                <div className="bg-surface-alt rounded p-2 text-center animate-pulse">
                  <div className="h-4 bg-gray-300 rounded mb-1"></div>
                  <div className="text-text-muted">Avg. Value</div>
                </div>
              </div>
              <div className="text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-text-muted">Last Order:</span>
                  <div className="h-3 w-16 bg-gray-300 rounded animate-pulse"></div>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Risk Level:</span>
                  <div className="h-3 w-12 bg-gray-300 rounded animate-pulse"></div>
                </div>
              </div>
            </div>
          ) : (
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
                  <span className="text-text-default">
                    {customerInsights.lastOrderDate 
                      ? new Date(customerInsights.lastOrderDate).toLocaleDateString()
                      : 'No orders yet'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Risk Level:</span>
                  <span className={`${
                    customerInsights.riskLevel === 'Low' ? 'text-state-success' :
                    customerInsights.riskLevel === 'Medium' ? 'text-yellow-600' :
                    customerInsights.riskLevel === 'High' ? 'text-state-error' :
                    'text-text-muted'
                  }`}>
                    {customerInsights.riskLevel}
                  </span>
                </div>
              </div>
              {customerInsights.preferredProducts.length > 0 && (
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
              )}
            </div>
          )}
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

        {/* AI Suggestions - Hidden for now */}
        {/*
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
        */}

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
              onClick={handleViewOrderHistory}
              className="w-full py-2 px-3 border border-border-subtle rounded-lg text-sm hover:bg-surface-alt transition-colors flex items-center justify-center space-x-2"
            >
              <TrendingUp className="w-4 h-4" />
              <span>View Order History</span>
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