'use client';

import { useState, useCallback } from 'react';
import { AIResponse } from '../types/message';

interface UseAIAgentOptions {
  distributorId: string;
}

interface AIOrderExtractionResult {
  confidence: number;
  extractedProducts: Array<{
    name: string;
    quantity: number;
    unit: string;
    unit_price?: number;
    catalog_match_id?: string;
  }>;
  requiresReview: boolean;
  extractedIntent: string;
}

interface AIMessageAnalysisResult {
  intent: string;
  confidence: number;
  suggestedResponses: string[];
  extractedData?: any;
  requiresFollowUp: boolean;
  sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
}

interface AICustomerInsightResult {
  summary: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  recommendations: string[];
  nextBestActions: string[];
}

interface UseAIAgentReturn {
  // State
  isProcessing: boolean;
  lastError: string | null;
  
  // Core AI functions
  processMessage: (content: string, conversationContext?: any) => Promise<AIMessageAnalysisResult>;
  extractOrderFromMessage: (content: string, customerContext?: any) => Promise<AIOrderExtractionResult>;
  generateResponseSuggestions: (messageContent: string, conversationHistory?: any[]) => Promise<string[]>;
  analyzeCustomerConversation: (conversationId: string) => Promise<AICustomerInsightResult>;
  
  // Utility functions
  detectOrderIntent: (content: string) => boolean;
  calculateConfidence: (result: any) => number;
  clearError: () => void;
}

export function useAIAgent({ distributorId }: UseAIAgentOptions): UseAIAgentReturn {
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);

  // Base API call function with error handling
  const callAIAPI = useCallback(async (endpoint: string, payload: any) => {
    try {
      setIsProcessing(true);
      setLastError(null);

      const response = await fetch(`/api/ai/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...payload,
          distributorId,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown AI processing error';
      setLastError(errorMessage);
      console.error('AI API Error:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [distributorId]);

  // Process a message for intent analysis and suggestions
  const processMessage = useCallback(async (
    content: string, 
    conversationContext?: any
  ): Promise<AIMessageAnalysisResult> => {
    try {
      const result = await callAIAPI('analyze-message', {
        content,
        conversationContext,
        tasks: ['intent_detection', 'response_generation', 'sentiment_analysis']
      });

      return {
        intent: result.intent || 'GENERAL_INQUIRY',
        confidence: result.confidence || 0.5,
        suggestedResponses: result.suggestedResponses || [],
        extractedData: result.extractedData,
        requiresFollowUp: result.requiresFollowUp || false,
        sentiment: result.sentiment || 'NEUTRAL'
      };
    } catch (error) {
      // Fallback to local processing if AI API fails
      console.warn('AI processing failed, using fallback logic');
      return {
        intent: detectOrderKeywords(content) ? 'ORDER_REQUEST' : 'GENERAL_INQUIRY',
        confidence: 0.3,
        suggestedResponses: generateFallbackResponses(content),
        requiresFollowUp: true,
        sentiment: 'NEUTRAL'
      };
    }
  }, [callAIAPI]);

  // Extract order information from message content
  const extractOrderFromMessage = useCallback(async (
    content: string, 
    customerContext?: any
  ): Promise<AIOrderExtractionResult> => {
    try {
      const result = await callAIAPI('extract-order', {
        content,
        customerContext,
        includeProductMatching: true,
        includePricing: true
      });

      return {
        confidence: result.confidence || 0,
        extractedProducts: result.extractedProducts || [],
        requiresReview: result.requiresReview !== false,
        extractedIntent: result.extractedIntent || 'ORDER_REQUEST'
      };
    } catch (error) {
      // Fallback to simple keyword extraction
      console.warn('Order extraction failed, using fallback logic');
      const products = extractProductsFromText(content);
      
      return {
        confidence: products.length > 0 ? 0.4 : 0,
        extractedProducts: products,
        requiresReview: true,
        extractedIntent: 'ORDER_REQUEST'
      };
    }
  }, [callAIAPI]);

  // Generate contextual response suggestions
  const generateResponseSuggestions = useCallback(async (
    messageContent: string, 
    conversationHistory?: any[]
  ): Promise<string[]> => {
    try {
      const result = await callAIAPI('generate-responses', {
        messageContent,
        conversationHistory: conversationHistory?.slice(-5), // Last 5 messages for context
        responseCount: 3,
        tone: 'professional'
      });

      return result.responses || [];
    } catch (error) {
      // Fallback to template-based responses
      console.warn('Response generation failed, using fallback templates');
      return generateFallbackResponses(messageContent);
    }
  }, [callAIAPI]);

  // Analyze conversation for customer insights
  const analyzeCustomerConversation = useCallback(async (
    conversationId: string
  ): Promise<AICustomerInsightResult> => {
    try {
      const result = await callAIAPI('analyze-customer', {
        conversationId,
        analysisDepth: 'standard',
        includeRecommendations: true
      });

      return {
        summary: result.summary || 'No analysis available',
        riskLevel: result.riskLevel || 'MEDIUM',
        recommendations: result.recommendations || [],
        nextBestActions: result.nextBestActions || []
      };
    } catch (error) {
      console.warn('Customer analysis failed');
      return {
        summary: 'Analysis temporarily unavailable',
        riskLevel: 'MEDIUM',
        recommendations: ['Follow up on recent messages', 'Check order history'],
        nextBestActions: ['Send product catalog', 'Offer assistance']
      };
    }
  }, [callAIAPI]);

  // Quick order intent detection (local function)
  const detectOrderIntent = useCallback((content: string): boolean => {
    return detectOrderKeywords(content);
  }, []);

  // Calculate confidence score
  const calculateConfidence = useCallback((result: any): number => {
    if (!result) return 0;
    
    // Simple confidence calculation based on result completeness
    let confidence = 0.5;
    
    if (result.extractedProducts?.length > 0) confidence += 0.2;
    if (result.intent && result.intent !== 'UNKNOWN') confidence += 0.1;
    if (result.suggestedResponses?.length > 0) confidence += 0.1;
    if (result.extractedData) confidence += 0.1;
    
    return Math.min(confidence, 1.0);
  }, []);

  // Clear error state
  const clearError = useCallback(() => {
    setLastError(null);
  }, []);

  return {
    isProcessing,
    lastError,
    processMessage,
    extractOrderFromMessage,
    generateResponseSuggestions,
    analyzeCustomerConversation,
    detectOrderIntent,
    calculateConfidence,
    clearError
  };
}

// Fallback functions for when AI API is unavailable

function detectOrderKeywords(content: string): boolean {
  const orderKeywords = [
    'order', 'need', 'want', 'buy', 'purchase', 'kg', 'kilos', 'boxes', 'units',
    'delivery', 'tomorrow', 'today', 'urgent', 'please send', 'can you',
    'vegetables', 'fruits', 'dairy', 'meat', 'bread', 'milk'
  ];
  
  const lowerContent = content.toLowerCase();
  return orderKeywords.some(keyword => lowerContent.includes(keyword));
}

function extractProductsFromText(content: string): Array<{
  name: string;
  quantity: number;
  unit: string;
  unit_price?: number;
}> {
  const products: any[] = [];
  const lowerContent = content.toLowerCase();
  
  // Simple regex patterns for common product requests
  const patterns = [
    /(\d+)\s*(kg|kilos?|pounds?)\s+(?:of\s+)?([a-zA-Z\s]+)/g,
    /(\d+)\s*(boxes?|units?|pieces?)\s+(?:of\s+)?([a-zA-Z\s]+)/g,
    /([a-zA-Z\s]+)\s*[:-]\s*(\d+)\s*(kg|units?|boxes?)/g
  ];
  
  patterns.forEach(pattern => {
    let match;
    while ((match = pattern.exec(lowerContent)) !== null) {
      const quantity = parseInt(match[1]);
      const unit = match[2];
      const name = match[3]?.trim();
      
      if (quantity && unit && name && name.length > 2) {
        products.push({
          name: name.charAt(0).toUpperCase() + name.slice(1),
          quantity,
          unit: unit.toLowerCase()
        });
      }
    }
  });
  
  return products;
}

function generateFallbackResponses(content: string): string[] {
  const lowerContent = content.toLowerCase();
  
  if (detectOrderKeywords(content)) {
    return [
      "I'd be happy to help you with your order. Could you please provide more details about the products you need?",
      "Thank you for your order request. Let me check our available products for you.",
      "I can help you place an order. What specific items are you looking for?"
    ];
  }
  
  if (lowerContent.includes('delivery') || lowerContent.includes('when')) {
    return [
      "Our standard delivery time is 24-48 hours for most orders.",
      "Let me check the delivery schedule for your area.",
      "Would you like me to track your current orders?"
    ];
  }
  
  if (lowerContent.includes('thank') || lowerContent.includes('thanks')) {
    return [
      "You're very welcome! Is there anything else I can help you with?",
      "Happy to help! Have a great day!",
      "Thank you for your business. Please don't hesitate to reach out if you need anything else."
    ];
  }
  
  if (lowerContent.includes('price') || lowerContent.includes('cost')) {
    return [
      "I can help you with pricing information. Which products are you interested in?",
      "Let me check current prices for you.",
      "Would you like to see our latest price list?"
    ];
  }
  
  return [
    "Thank you for your message. How can I assist you today?",
    "I'm here to help with any questions about our products or orders.",
    "Is there something specific I can help you with?"
  ];
}