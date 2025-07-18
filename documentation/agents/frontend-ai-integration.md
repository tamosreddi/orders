# Frontend AI Integration

## Overview

The frontend AI integration provides a seamless interface between the React/Next.js application and the AI agent system. It handles real-time AI processing, user interactions, and state management for all AI-powered features in the OrderAgent platform.

## Architecture

### Component Hierarchy
```
Messages Page (app/messages/page.tsx)
├── ChatList (components/ChatList.tsx)
├── MessageThread (components/MessageThread.tsx)
│   └── OrderContextCard (components/OrderContextCard.tsx)
└── AIAssistantPanel (components/AIAssistantPanel.tsx)

Hooks Layer
├── useMessages (hooks/useMessages.ts)
├── useAIAgent (hooks/useAIAgent.ts)
└── useWebSocket (hooks/useWebSocket.ts)
```

### State Management Flow
```
User Action → Hook → API Call → AI Processing → State Update → UI Re-render
```

## Core Components

### 1. **useAIAgent Hook**

**Location**: `app/messages/hooks/useAIAgent.ts`

The central hub for all AI operations in the frontend:

```typescript
interface UseAIAgentOptions {
  distributorId: string;
}

interface UseAIAgentReturn {
  // Processing state
  isProcessing: boolean;
  lastError: string | null;
  
  // Core AI functions
  processMessage: (content: string) => Promise<ProcessedMessage>;
  extractOrderFromMessage: (content: string) => Promise<OrderExtractionResult>;
  generateResponseSuggestions: (content: string, context: ConversationContext) => Promise<ResponseSuggestion[]>;
  analyzeCustomerConversation: (customerId: string, messages: Message[]) => Promise<CustomerInsights>;
  detectOrderIntent: (content: string) => boolean;
  
  // Usage tracking
  tokensUsed: number;
  costEstimate: number;
  requestCount: number;
}

const useAIAgent = ({ distributorId }: UseAIAgentOptions): UseAIAgentReturn => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [tokensUsed, setTokensUsed] = useState(0);
  const [costEstimate, setCostEstimate] = useState(0);
  const [requestCount, setRequestCount] = useState(0);
  
  // OpenAI client configuration
  const openai = new OpenAI({
    apiKey: process.env.NEXT_PUBLIC_OPENAI_API_KEY,
    dangerouslyAllowBrowser: true // Only for demo - use backend in production
  });
  
  const processMessage = async (content: string): Promise<ProcessedMessage> => {
    setIsProcessing(true);
    setLastError(null);
    
    try {
      const startTime = Date.now();
      
      // Step 1: Intent Detection
      const intentResponse = await openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [
          {
            role: "system",
            content: `Analyze this customer message and determine the primary intent.
            Return one of: ORDER_REQUEST, ORDER_INQUIRY, PRODUCT_INQUIRY, 
            SUPPORT_REQUEST, COMPLAINT, COMPLIMENT, GENERAL_INQUIRY`
          },
          {
            role: "user",
            content: content
          }
        ],
        max_tokens: 50,
        temperature: 0.1
      });
      
      const intent = intentResponse.choices[0].message.content?.trim() || 'GENERAL_INQUIRY';
      
      // Step 2: Entity Extraction (if applicable)
      let entities: ExtractedEntities = {
        products: [],
        quantities: [],
        dates: [],
        contacts: [],
        monetary: [],
        locations: []
      };
      
      if (intent === 'ORDER_REQUEST' || intent === 'PRODUCT_INQUIRY') {
        const entityResponse = await openai.chat.completions.create({
          model: "gpt-4",
          messages: [
            {
              role: "system",
              content: `Extract structured entities from this customer message.
              Return a JSON object with products, quantities, dates, contacts, 
              monetary values, and locations mentioned.`
            },
            {
              role: "user",
              content: content
            }
          ],
          response_format: { type: "json_object" },
          temperature: 0.1
        });
        
        try {
          entities = JSON.parse(entityResponse.choices[0].message.content || '{}');
        } catch (error) {
          console.warn('Failed to parse entity extraction result:', error);
        }
      }
      
      // Step 3: Sentiment Analysis
      const sentimentResponse = await openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [
          {
            role: "system",
            content: `Analyze the sentiment of this customer message.
            Return a JSON object with sentiment (POSITIVE, NEUTRAL, NEGATIVE, URGENT, CONFUSED),
            confidence (0-1), and urgency_level (LOW, MEDIUM, HIGH, CRITICAL).`
          },
          {
            role: "user",
            content: content
          }
        ],
        response_format: { type: "json_object" },
        temperature: 0.1
      });
      
      let sentiment: SentimentResult = {
        sentiment: 'NEUTRAL',
        confidence: 0.5,
        emotional_indicators: [],
        urgency_level: 'LOW'
      };
      
      try {
        sentiment = JSON.parse(sentimentResponse.choices[0].message.content || '{}');
      } catch (error) {
        console.warn('Failed to parse sentiment analysis result:', error);
      }
      
      // Track usage
      const totalTokens = (intentResponse.usage?.total_tokens || 0) + 
                         (entityResponse?.usage?.total_tokens || 0) + 
                         (sentimentResponse.usage?.total_tokens || 0);
      
      setTokensUsed(prev => prev + totalTokens);
      setCostEstimate(prev => prev + (totalTokens * 0.00003)); // Approximate cost
      setRequestCount(prev => prev + 1);
      
      const processingTime = Date.now() - startTime;
      
      // Store AI response for analytics
      await storeAIResponse({
        distributorId,
        agentType: 'message_processor',
        requestType: 'full_analysis',
        responseData: { intent, entities, sentiment },
        confidenceScore: sentiment.confidence,
        processingTimeMs: processingTime,
        tokensUsed: totalTokens,
        costUsd: totalTokens * 0.00003
      });
      
      return {
        original_message: content,
        intent,
        entities,
        sentiment,
        confidence: sentiment.confidence,
        processing_time_ms: processingTime,
        tokens_used: totalTokens
      };
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setLastError(errorMessage);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Additional AI functions...
  
  return {
    isProcessing,
    lastError,
    processMessage,
    extractOrderFromMessage,
    generateResponseSuggestions,
    analyzeCustomerConversation,
    detectOrderIntent,
    tokensUsed,
    costEstimate,
    requestCount
  };
};
```

### 2. **AIAssistantPanel Component**

**Location**: `app/messages/components/AIAssistantPanel.tsx`

The right-panel component that displays AI insights and suggestions:

```typescript
interface AIAssistantPanelProps {
  conversationId: string | null;
  conversation: Conversation | null;
  messages: Message[];
  onSendSuggestion: (suggestion: string) => void;
  onCreateOrder: () => void;
  onViewCustomerOrders: () => void;
}

const AIAssistantPanel: React.FC<AIAssistantPanelProps> = ({
  conversationId,
  conversation,
  messages,
  onSendSuggestion,
  onCreateOrder,
  onViewCustomerOrders
}) => {
  const [customerInsights, setCustomerInsights] = useState<CustomerInsights | null>(null);
  const [responseSuggestions, setResponseSuggestions] = useState<ResponseSuggestion[]>([]);
  const [orderAnalysis, setOrderAnalysis] = useState<OrderAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const { analyzeCustomerConversation, generateResponseSuggestions, detectOrderIntent } = useAIAgent({
    distributorId: 'dist_123' // Should come from auth context
  });
  
  // Analyze customer conversation when messages change
  useEffect(() => {
    if (conversation && messages.length > 0) {
      setIsAnalyzing(true);
      analyzeCustomerConversation(conversation.customerId, messages)
        .then(setCustomerInsights)
        .catch(console.error)
        .finally(() => setIsAnalyzing(false));
    }
  }, [conversation, messages, analyzeCustomerConversation]);
  
  // Generate response suggestions for the latest customer message
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.isFromCustomer) {
        generateResponseSuggestions(lastMessage.content, {
          conversationId: conversationId!,
          customerId: conversation?.customerId!,
          messages: messages.slice(-5) // Last 5 messages for context
        })
        .then(setResponseSuggestions)
        .catch(console.error);
      }
    }
  }, [messages, generateResponseSuggestions, conversationId, conversation]);
  
  // Check for order intent in the latest message
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.isFromCustomer && detectOrderIntent(lastMessage.content)) {
        // Trigger order analysis
        setOrderAnalysis({
          hasOrderIntent: true,
          confidence: 0.8,
          extractedProducts: [],
          estimatedValue: 0
        });
      }
    }
  }, [messages, detectOrderIntent]);
  
  if (!conversationId) {
    return (
      <div className="w-80 bg-gray-50 border-l border-gray-200 flex items-center justify-center">
        <p className="text-gray-500 text-center px-4">
          Select a conversation to see AI insights
        </p>
      </div>
    );
  }
  
  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
        {isAnalyzing && (
          <div className="mt-2 flex items-center text-sm text-blue-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            Analyzing conversation...
          </div>
        )}
      </div>
      
      {/* Customer Insights */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-medium text-gray-900 mb-3">Customer Insights</h3>
        
        {customerInsights ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Satisfaction</span>
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  customerInsights.satisfaction_score > 0.7 ? 'bg-green-500' :
                  customerInsights.satisfaction_score > 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span className="text-sm font-medium">
                  {(customerInsights.satisfaction_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Order History</span>
              <span className="text-sm font-medium">
                {customerInsights.total_orders} orders
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Avg Order Value</span>
              <span className="text-sm font-medium">
                ${customerInsights.avg_order_value.toFixed(2)}
              </span>
            </div>
            
            {customerInsights.risk_factors && (
              <div className="mt-3 p-3 bg-yellow-50 rounded-lg">
                <h4 className="text-sm font-medium text-yellow-800 mb-1">
                  Risk Factors
                </h4>
                <ul className="text-sm text-yellow-700 space-y-1">
                  {customerInsights.risk_factors.churn_risk > 0.7 && (
                    <li>• High churn risk</li>
                  )}
                  {customerInsights.risk_factors.payment_risk > 0.7 && (
                    <li>• Payment concerns</li>
                  )}
                  {customerInsights.risk_factors.satisfaction_risk > 0.7 && (
                    <li>• Low satisfaction</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm text-gray-500">
            No insights available yet
          </div>
        )}
      </div>
      
      {/* Order Detection */}
      {orderAnalysis?.hasOrderIntent && (
        <div className="p-4 border-b border-gray-200 bg-blue-50">
          <h3 className="font-medium text-blue-900 mb-2">Order Detected</h3>
          <p className="text-sm text-blue-700 mb-3">
            The customer appears to be placing an order.
          </p>
          <div className="space-y-2">
            <button
              onClick={onCreateOrder}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Create Order
            </button>
            <button
              onClick={onViewCustomerOrders}
              className="w-full px-3 py-2 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
            >
              View Order History
            </button>
          </div>
        </div>
      )}
      
      {/* Response Suggestions */}
      <div className="p-4 border-b border-gray-200 flex-1 overflow-y-auto">
        <h3 className="font-medium text-gray-900 mb-3">Suggested Responses</h3>
        
        {responseSuggestions.length > 0 ? (
          <div className="space-y-2">
            {responseSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSendSuggestion(suggestion.content)}
                className="w-full text-left p-3 rounded border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <div className="font-medium text-gray-900 text-sm mb-1">
                  {suggestion.title}
                </div>
                <div className="text-gray-600 text-xs line-clamp-2">
                  {suggestion.preview}
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-500 capitalize">
                    {suggestion.tone.toLowerCase()}
                  </span>
                  <span className="text-xs text-gray-500">
                    {(suggestion.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500">
            No suggestions available
          </div>
        )}
      </div>
      
      {/* Quick Actions */}
      <div className="p-4 border-t border-gray-200">
        <h3 className="font-medium text-gray-900 mb-3">Quick Actions</h3>
        <div className="space-y-2">
          <button
            onClick={onCreateOrder}
            className="w-full px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700"
          >
            New Order
          </button>
          <button
            onClick={onViewCustomerOrders}
            className="w-full px-4 py-2 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
          >
            Order History
          </button>
        </div>
      </div>
    </div>
  );
};
```

### 3. **OrderContextCard Component**

**Location**: `app/messages/components/OrderContextCard.tsx`

Inline order cards that appear in the message thread:

```typescript
interface OrderContextCardProps {
  extractedOrder: OrderExtractionResult;
  onApprove: (orderId: string) => void;
  onReject: (orderId: string) => void;
  onModify: (orderId: string) => void;
}

const OrderContextCard: React.FC<OrderContextCardProps> = ({
  extractedOrder,
  onApprove,
  onReject,
  onModify
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const confidenceColor = extractedOrder.confidence > 0.8 ? 'green' : 
                         extractedOrder.confidence > 0.6 ? 'yellow' : 'red';
  
  return (
    <div className="border border-blue-200 rounded-lg p-4 bg-blue-50 my-2">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-blue-900">Order Detected</h4>
        <div className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded-full bg-${confidenceColor}-500`} />
          <span className="text-sm text-blue-700">
            {(extractedOrder.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>
      </div>
      
      <div className="space-y-2 mb-3">
        <div className="text-sm">
          <span className="font-medium text-blue-900">Products:</span>
          <span className="text-blue-700 ml-2">
            {extractedOrder.extractedProducts.length} items
          </span>
        </div>
        
        <div className="text-sm">
          <span className="font-medium text-blue-900">Estimated Total:</span>
          <span className="text-blue-700 ml-2">
            ${extractedOrder.pricing.total.toFixed(2)}
          </span>
        </div>
        
        {extractedOrder.deliveryInfo.delivery_date && (
          <div className="text-sm">
            <span className="font-medium text-blue-900">Delivery:</span>
            <span className="text-blue-700 ml-2">
              {extractedOrder.deliveryInfo.delivery_date}
            </span>
          </div>
        )}
      </div>
      
      {isExpanded && (
        <div className="border-t border-blue-200 pt-3 mb-3">
          <h5 className="font-medium text-blue-900 mb-2">Order Details</h5>
          <div className="space-y-2">
            {extractedOrder.extractedProducts.map((product, index) => (
              <div key={index} className="flex justify-between items-center text-sm">
                <span className="text-blue-700">{product.product_name}</span>
                <span className="text-blue-700">
                  {extractedOrder.quantities[index]?.normalized_quantity || 0} x 
                  ${product.unit_price?.toFixed(2) || '0.00'}
                </span>
              </div>
            ))}
          </div>
          
          {extractedOrder.validation.validation_errors.length > 0 && (
            <div className="mt-3 p-2 bg-red-50 rounded border border-red-200">
              <h6 className="font-medium text-red-900 text-sm mb-1">Issues Found</h6>
              <ul className="text-sm text-red-700 space-y-1">
                {extractedOrder.validation.validation_errors.map((error, index) => (
                  <li key={index}>• {error.message}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
      <div className="flex items-center gap-2">
        <button
          onClick={() => onApprove(extractedOrder.order_id)}
          className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
        >
          Approve Order
        </button>
        
        <button
          onClick={() => onModify(extractedOrder.order_id)}
          className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700"
        >
          Modify
        </button>
        
        <button
          onClick={() => onReject(extractedOrder.order_id)}
          className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Reject
        </button>
        
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
        >
          {isExpanded ? 'Show Less' : 'Show Details'}
        </button>
      </div>
    </div>
  );
};
```

## State Management

### React Context for AI State

```typescript
interface AIContextState {
  isProcessing: boolean;
  currentModel: string;
  tokensUsed: number;
  costEstimate: number;
  errorMessage: string | null;
  processingQueue: string[];
}

const AIContext = createContext<{
  state: AIContextState;
  dispatch: React.Dispatch<AIAction>;
} | null>(null);

const aiReducer = (state: AIContextState, action: AIAction): AIContextState => {
  switch (action.type) {
    case 'START_PROCESSING':
      return {
        ...state,
        isProcessing: true,
        errorMessage: null,
        processingQueue: [...state.processingQueue, action.payload.requestId]
      };
      
    case 'FINISH_PROCESSING':
      return {
        ...state,
        isProcessing: state.processingQueue.length <= 1,
        processingQueue: state.processingQueue.filter(id => id !== action.payload.requestId),
        tokensUsed: state.tokensUsed + action.payload.tokensUsed,
        costEstimate: state.costEstimate + action.payload.cost
      };
      
    case 'SET_ERROR':
      return {
        ...state,
        errorMessage: action.payload.message,
        isProcessing: false
      };
      
    default:
      return state;
  }
};

export const AIProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(aiReducer, {
    isProcessing: false,
    currentModel: 'gpt-4',
    tokensUsed: 0,
    costEstimate: 0,
    errorMessage: null,
    processingQueue: []
  });
  
  return (
    <AIContext.Provider value={{ state, dispatch }}>
      {children}
    </AIContext.Provider>
  );
};
```

## Real-time Updates

### WebSocket Integration

```typescript
const useAIWebSocket = (conversationId: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  
  useEffect(() => {
    if (!conversationId) return;
    
    const ws = new WebSocket(`ws://localhost:3001/ai-updates/${conversationId}`);
    
    ws.onopen = () => {
      setConnectionStatus('connected');
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'AI_ANALYSIS_COMPLETE':
          // Update customer insights
          handleAIAnalysisComplete(data.payload);
          break;
          
        case 'ORDER_DETECTED':
          // Show order context card
          handleOrderDetected(data.payload);
          break;
          
        case 'RESPONSE_SUGGESTIONS':
          // Update response suggestions
          handleResponseSuggestions(data.payload);
          break;
      }
    };
    
    ws.onclose = () => {
      setConnectionStatus('disconnected');
      setSocket(null);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('disconnected');
    };
    
    return () => {
      ws.close();
    };
  }, [conversationId]);
  
  const sendMessage = (type: string, payload: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type, payload }));
    }
  };
  
  return { connectionStatus, sendMessage };
};
```

## Performance Optimization

### Debounced AI Processing

```typescript
const useDebouncedAI = (delay: number = 1000) => {
  const [debouncedRequests, setDebouncedRequests] = useState<Map<string, any>>(new Map());
  
  const processWithDebounce = useCallback(
    debounce(async (key: string, processor: () => Promise<any>) => {
      try {
        const result = await processor();
        setDebouncedRequests(prev => new Map(prev.set(key, result)));
      } catch (error) {
        console.error('Debounced AI processing error:', error);
      }
    }, delay),
    [delay]
  );
  
  return { processWithDebounce, debouncedRequests };
};
```

### Memoized AI Results

```typescript
const useMemoizedAI = () => {
  const cache = useMemo(() => new Map<string, any>(), []);
  
  const getCachedResult = useCallback((key: string) => {
    return cache.get(key);
  }, [cache]);
  
  const setCachedResult = useCallback((key: string, value: any) => {
    cache.set(key, value);
    
    // Cleanup old entries (keep last 100)
    if (cache.size > 100) {
      const firstKey = cache.keys().next().value;
      cache.delete(firstKey);
    }
  }, [cache]);
  
  return { getCachedResult, setCachedResult };
};
```

## Error Handling

### Error Boundary for AI Components

```typescript
class AIErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('AI Component Error:', error, errorInfo);
    
    // Log to analytics
    logAIError({
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    });
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <h3 className="font-medium text-red-900 mb-2">AI Service Error</h3>
          <p className="text-sm text-red-700">
            The AI assistant is temporarily unavailable. Please try again in a moment.
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

## Testing

### AI Hook Testing

```typescript
import { renderHook, act } from '@testing-library/react';
import { useAIAgent } from '../hooks/useAIAgent';

describe('useAIAgent', () => {
  const mockOpenAI = {
    chat: {
      completions: {
        create: jest.fn()
      }
    }
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('should process message and return structured result', async () => {
    mockOpenAI.chat.completions.create.mockResolvedValue({
      choices: [{ message: { content: 'ORDER_REQUEST' } }],
      usage: { total_tokens: 100 }
    });
    
    const { result } = renderHook(() => useAIAgent({ distributorId: 'test' }));
    
    await act(async () => {
      const processed = await result.current.processMessage('I need 10 apples');
      expect(processed.intent).toBe('ORDER_REQUEST');
      expect(processed.confidence).toBeGreaterThan(0);
    });
  });
  
  test('should handle processing errors gracefully', async () => {
    mockOpenAI.chat.completions.create.mockRejectedValue(new Error('API Error'));
    
    const { result } = renderHook(() => useAIAgent({ distributorId: 'test' }));
    
    await act(async () => {
      await expect(result.current.processMessage('test')).rejects.toThrow('API Error');
    });
    
    expect(result.current.lastError).toBe('API Error');
  });
});
```

### Component Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { AIAssistantPanel } from '../components/AIAssistantPanel';

describe('AIAssistantPanel', () => {
  const mockProps = {
    conversationId: 'test-conv',
    conversation: { customerId: 'test-customer' },
    messages: [{ content: 'Hello', isFromCustomer: true }],
    onSendSuggestion: jest.fn(),
    onCreateOrder: jest.fn(),
    onViewCustomerOrders: jest.fn()
  };
  
  test('should render customer insights when available', () => {
    render(<AIAssistantPanel {...mockProps} />);
    
    expect(screen.getByText('Customer Insights')).toBeInTheDocument();
  });
  
  test('should handle suggestion clicks', () => {
    render(<AIAssistantPanel {...mockProps} />);
    
    const suggestionButton = screen.getByText('Suggested Responses');
    fireEvent.click(suggestionButton);
    
    expect(mockProps.onSendSuggestion).toHaveBeenCalled();
  });
});
```

## Deployment Considerations

### Environment Variables

```typescript
// .env.local
NEXT_PUBLIC_OPENAI_API_KEY=sk-...
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_AI_WEBSOCKET_URL=ws://localhost:3001

// Production security note:
// Never expose OpenAI API keys in frontend code
// Use backend proxy for production deployments
```

### Build Optimizations

```javascript
// next.config.js
const nextConfig = {
  experimental: {
    optimizePackageImports: ['@openai/api']
  },
  webpack: (config) => {
    // Optimize bundle size for AI libraries
    config.resolve.alias = {
      ...config.resolve.alias,
      'openai': 'openai/dist/index.mjs'
    };
    return config;
  }
};
```

---

*The frontend AI integration provides a seamless, real-time interface for AI-powered features while maintaining performance and user experience standards.*