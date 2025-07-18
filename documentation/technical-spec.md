# Technical Specification - Messages Page with AI Integration

## AI Agent Architecture

### Pydantic AI Framework Integration

This implementation leverages your established `agent-platform/` framework with Pydantic AI agents and MCP (Model Context Protocol) tools for seamless integration with Supabase and Context7.

**Core Architecture:**
```
Frontend (Next.js) ↔ Backend API (FastAPI) ↔ Pydantic AI Agents ↔ MCP Tools
                                                ├── Supabase MCP (Database operations)
                                                └── Context7 MCP (Context management)
```

### Pydantic AI Agents (using your agent_template.py pattern)

1. **Message Analysis Agent** (`agents/message_analysis.py`)
   - Processes incoming messages for intent classification and PII detection
   - Uses Context7 MCP for conversation history analysis
   - Leverages Supabase MCP to access customer data and order history
   - Outputs: Intent classification, confidence scores, suggested actions

2. **Order Processing Agent** (`agents/order_processing.py`)
   - Handles order-related requests and creates structured order data
   - Processes WhatsApp messages, images, and even voice messages
   - Uses Supabase MCP to match products from the catalog (`products` table)
   - Creates orders with proper multi-tenant isolation (`distributor_id`)
   - Outputs: Structured orders with line items, confidence tracking

3. **Customer Support Agent** (`agents/customer_support.py`)
   - Provides intelligent responses to customer queries
   - Accesses customer history via Supabase MCP (`customers`, `orders`, `conversations`)
   - Uses Context7 MCP for maintaining conversation context
   - Integrates with product catalog for accurate recommendations

4. **Context Manager** (`agents/context_manager.py`)
   - Maintains conversation history and customer context across sessions
   - Uses Context7 MCP for advanced context retrieval and storage
   - Manages AI usage tracking and cost monitoring via Supabase MCP
   - Handles multi-tenant context isolation

### Enhanced Agent Capabilities with Database Integration

- Natural language order processing with product catalog matching
- Customer query resolution with full order history access
- Automated order status updates with multi-tenant security
- Intelligent message routing based on customer classification
- Contextual suggestions using conversation history and customer preferences
- Real-time AI usage and cost tracking per distributor
- Advanced product matching using aliases and keywords from catalog

## Data Architecture

### Enhanced Multi-Tenant Database Schema

The platform uses a comprehensive multi-tenant database with 16 tables supporting AI-powered operations. All data is isolated by `distributor_id` for complete business separation.

### Core Data Types (Enhanced with Database Integration)

```ts
// Messages with AI processing metadata
export interface Message {
  id: string;
  conversationId: string;
  content: string;
  isFromCustomer: boolean;
  messageType: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT';
  status: 'SENT' | 'DELIVERED' | 'READ';
  
  // AI Processing Fields
  aiProcessed: boolean;
  aiConfidence?: number;
  aiExtractedIntent?: string;
  aiExtractedProducts?: any[];
  aiSuggestedResponses?: string[];
  
  // Order Context
  orderContextId?: string;
  
  // Metadata
  attachments: any[];
  externalMessageId?: string;
  createdAt: string;
  updatedAt: string;
}

// Conversations grouping messages by customer/channel
export interface Conversation {
  id: string;
  customerId: string;
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  status: 'ACTIVE' | 'ARCHIVED';
  lastMessageAt?: string;
  unreadCount: number;
  aiContextSummary?: string;
  distributorId: string;
}

// Enhanced Customer with multi-tenant support
export interface Customer {
  id: string;
  businessName: string;
  contactPersonName?: string;
  customerCode: string;
  email: string;
  phone?: string;
  address?: string;
  avatarUrl?: string;
  
  // Status tracking
  status: 'ORDERING' | 'AT_RISK' | 'STOPPED_ORDERING' | 'NO_ORDERS_YET';
  invitationStatus: 'ACTIVE' | 'PENDING';
  
  // Aggregated data (auto-calculated via triggers)
  totalOrders: number;
  totalSpent: number;
  lastOrderedDate?: string;
  
  // Multi-tenant
  distributorId: string;
  
  // Labels relationship
  labels: CustomerLabel[];
}

// Orders with AI generation tracking
export interface Order {
  id: string;
  customerId: string;
  conversationId?: string;
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  status: 'CONFIRMED' | 'PENDING' | 'REVIEW';
  
  // AI metadata
  aiGenerated: boolean;
  aiConfidence?: number;
  aiSourceMessageId?: string;
  requiresReview: boolean;
  
  // Order details
  receivedDate: string;
  receivedTime: string;
  deliveryDate?: string;
  totalAmount: number;
  
  // Multi-tenant
  distributorId: string;
  
  // Related data
  products: OrderProduct[];
  attachments: OrderAttachment[];
}

// AI Responses tracking
export interface AIResponse {
  id: string;
  messageId: string;
  agentType: 'ORDER_PROCESSING' | 'CUSTOMER_SUPPORT' | 'MESSAGE_ANALYSIS' | 'CONTEXT_MANAGER';
  responseContent: string;
  confidence?: number;
  extractedData?: any;
  tokensUsed?: number;
  modelUsed: string;
  humanFeedback?: 'HELPFUL' | 'PARTIALLY_HELPFUL' | 'NOT_HELPFUL';
  createdAt: string;
}
```

### Database Tables Overview

- **Core Tables**: `distributors`, `customers`, `conversations`, `messages`, `orders`, `order_products`
- **AI Tables**: `ai_responses`, `ai_usage_metrics`, `ai_training_data`, `ai_errors`
- **Security Tables**: `data_access_audit`, `pii_detection_results`, `encryption_keys`
- **Integration Tables**: `webhook_endpoints`, `webhook_deliveries`, `external_integrations`
- **Product Tables**: `products`, `product_categories`, `product_variants` (future catalog)

### Multi-Tenant Architecture

- Every table includes `distributor_id` for complete data isolation
- Row Level Security (RLS) policies enforce tenant boundaries
- All queries automatically filtered by current distributor context

## AI Agent Implementation

### Pydantic AI + MCP Integration Pattern

Using your established `agent-platform/` framework with automatic MCP tool integration:

```python
# Backend implementation using your agent_template.py pattern
from agent_platform.agent_template import get_pydantic_ai_agent
from agent_platform.mcp_client import MCPClient

async def initialize_message_agents():
    """Initialize all AI agents with MCP tools"""
    client, base_agent = await get_pydantic_ai_agent()
    
    # Agents automatically get Supabase MCP and Context7 MCP tools
    message_agent = base_agent.with_system_prompt(MESSAGE_ANALYSIS_PROMPT)
    order_agent = base_agent.with_system_prompt(ORDER_PROCESSING_PROMPT)
    support_agent = base_agent.with_system_prompt(CUSTOMER_SUPPORT_PROMPT)
    
    return {
        'message_analysis': message_agent,
        'order_processing': order_agent,
        'customer_support': support_agent,
        'client': client
    }
```

### Backend Architecture (FastAPI + Pydantic AI)

- **FastAPI Server**: REST API endpoints for frontend communication
- **Pydantic AI Agents**: Your `agent_template.py` pattern with MCP tools
- **Automatic Database Access**: Supabase MCP handles all database operations
- **Context Management**: Context7 MCP for conversation context
- **Multi-tenant Security**: Automatic `distributor_id` filtering via RLS

### Key Implementation Benefits

- **No Direct Database Queries**: All DB operations through Supabase MCP
- **Type Safety**: Pydantic models ensure data validation
- **Automatic Tool Integration**: MCP tools available to all agents
- **Cost Tracking**: Built-in AI usage monitoring via database triggers
- **Error Handling**: Graceful degradation when AI services are unavailable
- **Multi-tenant Isolation**: Automatic enforcement via database RLS policies

## Real-time Features

- **WebSocket Connection**: Implement for live message updates and typing indicators
- **Message Queuing**: Handle message ordering and delivery confirmation
- **Offline Support**: Cache messages locally with sync when reconnected

## Platform Integration

- **Design Continuity**: Reuse existing components from Orders and Customers pages
- **Navigation**: Seamless transitions between Messages, Orders, and Customers
- **Shared State**: Integrate with existing customer and order data stores
- **Responsive Design**: Ensure mobile-first approach matching current platform

## OrderReview Integration Flow

### AI-Generated Orders to OrderReview Table

**Data Flow Architecture:**
```
Customer Message → Order Processing Agent → AI Extracted Products → OrderReview Components
     ↓                        ↓                      ↓                        ↓
WhatsApp/SMS/Email    Pydantic AI Analysis    Structured OrderProduct[]    EditableProductsTable
```

### Data Transformation Pipeline

**1. AI Order Processing Agent Output:**
```python
# agents/order_processing.py - AI agent output
class AIOrderResponse(BaseModel):
    """AI agent response for order processing"""
    confidence: float
    extracted_products: List[Dict[str, Any]]
    customer_id: str
    conversation_id: str
    source_message_id: str
    requires_review: bool
    
    # Example extracted_products structure:
    # [
    #   {
    #     "name": "Tomates ecológicos",
    #     "quantity": 5,
    #     "unit": "kg", 
    #     "unit_price": 3.50,
    #     "confidence": 0.95,
    #     "catalog_match_id": "prod_123"
    #   }
    # ]
```

**2. Data Transformation to OrderProduct[]:**
```typescript
// lib/orderTransformers.ts
import { OrderProduct } from '../types/order';

interface AIExtractedProduct {
  name: string;
  quantity: number;
  unit: string;
  unit_price: number;
  confidence: number;
  catalog_match_id?: string;
}

export function transformAIProductsToOrderProducts(
  aiProducts: AIExtractedProduct[]
): OrderProduct[] {
  return aiProducts.map((product, index) => ({
    id: product.catalog_match_id || `AI_${Date.now()}_${index}`,
    name: product.name,
    unit: product.unit,
    quantity: product.quantity,
    unitPrice: product.unit_price,
    linePrice: product.quantity * product.unit_price,
    // AI metadata for tracking
    aiGenerated: true,
    aiConfidence: product.confidence,
    catalogMatchId: product.catalog_match_id
  }));
}
```

**3. Messages Page to OrderReview Navigation:**
```typescript
// app/messages/components/OrderContextCard.tsx
interface OrderContextCardProps {
  message: Message;
  aiExtractedProducts?: any[];
}

export function OrderContextCard({ message, aiExtractedProducts }: OrderContextCardProps) {
  const router = useRouter();
  
  const handleCreateOrder = async () => {
    if (!aiExtractedProducts) return;
    
    // Transform AI products to OrderProduct format
    const orderProducts = transformAIProductsToOrderProducts(aiExtractedProducts);
    
    // Create draft order in database
    const draftOrder = await createDraftOrder({
      customerId: message.conversationId, // map to customer
      products: orderProducts,
      aiSourceMessageId: message.id,
      requiresReview: true,
      aiGenerated: true
    });
    
    // Navigate to OrderReview with pre-populated data
    router.push(`/orders/review/${draftOrder.id}`);
  };
  
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-2">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium text-blue-900">
            Order Detected {aiExtractedProducts?.length} products
          </h4>
          <p className="text-xs text-blue-600">
            AI Confidence: {message.aiConfidence}%
          </p>
        </div>
        <button
          onClick={handleCreateOrder}
          className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
        >
          Review Order
        </button>
      </div>
    </div>
  );
}
```

### API Integration Points

**Backend Endpoints for Order Flow:**
```python
# backend/routers/orders.py
from fastapi import APIRouter, Depends
from ..models.order import OrderCreate, OrderResponse
from ..services.agent_service import OrderProcessingService

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/from-message")
async def create_order_from_message(
    message_id: str,
    distributor_id: str = Depends(get_current_distributor)
) -> OrderResponse:
    """Create order from AI-processed message"""
    
    # Get AI analysis for the message
    ai_response = await get_ai_response_for_message(message_id)
    
    if not ai_response or not ai_response.extracted_products:
        raise HTTPException(status_code=400, detail="No products extracted from message")
    
    # Transform AI products to order format
    order_products = transform_ai_products_to_order_products(
        ai_response.extracted_products
    )
    
    # Create draft order
    draft_order = await create_draft_order(
        customer_id=ai_response.customer_id,
        conversation_id=ai_response.conversation_id,
        products=order_products,
        ai_source_message_id=message_id,
        requires_review=ai_response.requires_review,
        distributor_id=distributor_id
    )
    
    return OrderResponse.from_orm(draft_order)

@router.get("/review/{order_id}")
async def get_order_for_review(
    order_id: str,
    distributor_id: str = Depends(get_current_distributor)
) -> OrderResponse:
    """Get order data for review page"""
    
    order = await get_order_with_products(order_id, distributor_id)
    return OrderResponse.from_orm(order)
```

### OrderReview Page Integration

**Enhanced OrderReview Page:**
```typescript
// app/orders/review/[orderId]/page.tsx
interface OrderReviewPageProps {
  params: { orderId: string };
}

export default function OrderReviewPage({ params }: OrderReviewPageProps) {
  const [order, setOrder] = useState<Order | null>(null);
  const [products, setProducts] = useState<OrderProduct[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    async function loadOrder() {
      try {
        const orderData = await fetch(`/api/orders/review/${params.orderId}`);
        const orderJson = await orderData.json();
        
        setOrder(orderJson);
        setProducts(orderJson.products || []);
        
        // Show AI generation notice if applicable
        if (orderJson.aiGenerated) {
          showAIGenerationNotice(orderJson);
        }
      } catch (error) {
        console.error('Failed to load order:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadOrder();
  }, [params.orderId]);
  
  const handleProductsChange = (updatedProducts: OrderProduct[]) => {
    setProducts(updatedProducts);
  };
  
  const handleSaveOrder = async () => {
    await updateOrder(params.orderId, {
      products: products,
      status: 'CONFIRMED',
      requiresReview: false
    });
    
    router.push('/orders');
  };
  
  return (
    <div className="container mx-auto p-6">
      {order?.aiGenerated && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <span className="text-blue-600 text-sm font-medium">
              🤖 AI-Generated Order
            </span>
            <span className="text-blue-500 text-xs">
              Confidence: {order.aiConfidence}% | Source: Message #{order.aiSourceMessageId}
            </span>
          </div>
          <p className="text-blue-600 text-xs mt-1">
            Please review the extracted products and make any necessary adjustments.
          </p>
        </div>
      )}
      
      <EditableProductsTable
        products={products}
        onProductsChange={handleProductsChange}
      />
      
      <div className="mt-6 flex justify-end space-x-4">
        <button
          onClick={() => router.back()}
          className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSaveOrder}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Confirm Order
        </button>
      </div>
    </div>
  );
}
```

### State Management Flow

**Messages ↔ OrderReview State Sharing:**
```typescript
// lib/stores/orderStore.ts
interface OrderDraft {
  id: string;
  customerId: string;
  conversationId?: string;
  products: OrderProduct[];
  aiGenerated: boolean;
  aiSourceMessageId?: string;
  requiresReview: boolean;
}

export const useOrderStore = create<{
  draftOrders: OrderDraft[];
  createDraftFromMessage: (messageId: string, aiProducts: any[]) => Promise<string>;
  getDraft: (orderId: string) => OrderDraft | null;
  updateDraft: (orderId: string, updates: Partial<OrderDraft>) => void;
}>((set, get) => ({
  draftOrders: [],
  
  createDraftFromMessage: async (messageId: string, aiProducts: any[]) => {
    const orderProducts = transformAIProductsToOrderProducts(aiProducts);
    
    const draft: OrderDraft = {
      id: `draft_${Date.now()}`,
      customerId: '', // derived from message
      products: orderProducts,
      aiGenerated: true,
      aiSourceMessageId: messageId,
      requiresReview: true
    };
    
    set(state => ({
      draftOrders: [...state.draftOrders, draft]
    }));
    
    return draft.id;
  },
  
  getDraft: (orderId: string) => {
    return get().draftOrders.find(draft => draft.id === orderId) || null;
  },
  
  updateDraft: (orderId: string, updates: Partial<OrderDraft>) => {
    set(state => ({
      draftOrders: state.draftOrders.map(draft =>
        draft.id === orderId ? { ...draft, ...updates } : draft
      )
    }));
  }
}));
```

### Error Handling & Edge Cases

**AI Confidence Thresholds:**
```typescript
// lib/aiValidation.ts
export function validateAIOrderExtraction(
  aiResponse: AIOrderResponse
): { isValid: boolean; warnings: string[] } {
  const warnings: string[] = [];
  
  // Check overall confidence
  if (aiResponse.confidence < 0.8) {
    warnings.push('Low AI confidence - manual review recommended');
  }
  
  // Check individual product confidence
  const lowConfidenceProducts = aiResponse.extracted_products.filter(
    product => product.confidence < 0.7
  );
  
  if (lowConfidenceProducts.length > 0) {
    warnings.push(`${lowConfidenceProducts.length} products have low confidence scores`);
  }
  
  // Check for missing prices
  const missingPrices = aiResponse.extracted_products.filter(
    product => !product.unit_price || product.unit_price <= 0
  );
  
  if (missingPrices.length > 0) {
    warnings.push(`${missingPrices.length} products missing pricing information`);
  }
  
  return {
    isValid: warnings.length === 0 || aiResponse.confidence > 0.6,
    warnings
  };
}
```

This integration ensures seamless data flow from AI-processed messages to the existing OrderReview table components, maintaining data integrity and providing clear user feedback about AI-generated content.

## Performance Optimization

- **Message Virtualization**: For large conversation histories
- **Lazy Loading**: Load conversation history incrementally
- **Caching Strategy**: Implement efficient message and AI response caching
- **Bundle Optimization**: Code splitting for AI features

## File Structure (Detailed)

### Frontend (Next.js 14 App Router)

```
/app/messages/
  ├── page.tsx                    # Main messages page
  ├── components/
  │   ├── ChatList.tsx           # Left sidebar with conversations
  │   ├── MessageThread.tsx      # Central message display
  │   ├── AIAssistantPanel.tsx   # Right sidebar with AI features
  │   ├── MessageInput.tsx       # Message composition area
  │   ├── OrderContextCard.tsx   # Inline order summaries
  │   └── ChannelIndicator.tsx   # Channel-specific styling
  ├── hooks/
  │   ├── useMessages.ts         # Message data management via API
  │   ├── useAIAgent.ts          # AI agent communication via API
  │   └── useWebSocket.ts        # Real-time updates
  └── types/
      ├── message.ts             # Enhanced message types
      ├── conversation.ts        # Conversation types
      └── aiAgent.ts             # AI agent response types

/lib/
  ├── api.ts                     # API client for backend communication
  ├── messageHelpers.ts          # Frontend message utilities
  └── supabase.ts               # Supabase client (for real-time features)
```

### Backend (Python FastAPI + Pydantic AI)

```
/backend/
  ├── main.py                    # FastAPI application entry point
  ├── routers/
  │   ├── messages.py           # Message endpoints
  │   ├── conversations.py      # Conversation endpoints
  │   ├── ai_agents.py          # AI agent endpoints
  │   └── webhook.py            # Webhook handling (WhatsApp, SMS, Email)
  ├── agents/
  │   ├── message_analysis.py   # Message analysis Pydantic AI agent
  │   ├── order_processing.py   # Order processing Pydantic AI agent
  │   ├── customer_support.py   # Customer support Pydantic AI agent
  │   └── context_manager.py    # Context management agent
  ├── models/
  │   ├── message.py            # Pydantic models for messages
  │   ├── conversation.py       # Pydantic models for conversations
  │   ├── order.py              # Pydantic models for orders
  │   └── ai_response.py        # Pydantic models for AI responses
  ├── services/
  │   ├── agent_service.py      # AI agent orchestration
  │   ├── webhook_service.py    # External webhook processing
  │   └── realtime_service.py   # WebSocket/real-time features
  ├── config/
  │   ├── settings.py           # Application settings
  │   ├── prompts.py            # AI agent prompts
  │   └── mcp_config.py         # MCP configuration
  └── requirements.txt          # Python dependencies

/agent-platform/              # Your existing framework (reused)
  ├── agent_template.py         # Pydantic AI agent template
  ├── mcp_client.py            # MCP client implementation
  ├── mcp_config.json          # MCP configuration (Supabase + Context7)
  └── requirements.txt         # Framework dependencies
```

### Integration Architecture

- **Frontend**: Next.js calls FastAPI backend via REST API
- **Backend**: FastAPI orchestrates Pydantic AI agents with MCP tools
- **Database**: All operations through Supabase MCP (no direct queries)
- **Real-time**: Supabase real-time subscriptions for live updates
- **AI Processing**: Pydantic AI agents with automatic tool integration

## Testing Strategy

- **Unit Tests**: Message processing, AI agent responses, and utility functions
- **Integration Tests**: OpenAI API interactions and WebSocket connections
- **E2E Tests**: Complete conversation flows and order processing workflows
- **Performance Tests**: Message rendering and AI response times

## AI Monitoring & Cost Tracking

### Built-in AI Performance Monitoring

The enhanced database schema includes comprehensive AI monitoring and cost tracking:

**Usage Tracking (`ai_usage_metrics` table):**
- **Hourly granularity**: Track AI requests, costs, and performance per hour
- **Per-distributor tracking**: Each business monitors their own AI usage
- **Cost control**: Monthly budget limits with automatic alerts
- **Model performance**: Track confidence scores and response times

**AI Response Quality (`ai_responses` table):**
- **Response tracking**: Every AI interaction logged with metadata
- **Human feedback**: Users rate AI responses for continuous improvement
- **Confidence monitoring**: Track AI confidence levels over time
- **Error tracking**: Failed AI requests logged for debugging

**Cost Management Features:**
```python
# Automatic cost tracking via database triggers
# Example AI usage monitoring:
{
  "distributor_id": "dist_123",
  "date": "2024-07-17",
  "hour": 14,
  "requests_count": 150,
  "successful_requests": 145,
  "cost_cents": 1250,  # $12.50
  "total_tokens": 50000,
  "avg_confidence": 0.85,
  "avg_response_time_ms": 750
}
```

**AI Budget Controls:**
- **Monthly limits**: Configurable AI spending limits per distributor
- **Alert system**: Automatic notifications when approaching budget limits
- **Usage analytics**: Detailed breakdowns by agent type and time period
- **Cost optimization**: Identify high-cost operations for optimization

**Performance Analytics:**
- **Agent efficiency**: Compare performance across different AI agent types
- **Response quality trends**: Track improvement in AI responses over time
- **Customer satisfaction**: Correlate AI responses with customer feedback
- **Training data collection**: Poor responses automatically become training data

## Future Enhancements

- **Multi-language Support**: AI agents with language detection and translation
- **Voice Messages**: Audio message transcription and processing
- **Advanced Analytics**: Conversation insights and customer behavior analysis
- **Webhook Integration**: External system notifications and integrations
- **AI Model Fine-tuning**: Custom model training based on collected feedback
- **Predictive Analytics**: Customer behavior prediction and recommendation engine