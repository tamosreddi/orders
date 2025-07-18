# AI Agent Architecture

## System Overview

The OrderAgent platform implements a sophisticated multi-agent AI system designed for B2B order processing and customer service automation. The architecture follows a distributed design with clear separation between frontend interfaces, backend processing, and data persistence.

## Core Architecture Patterns

### 1. **Agent-as-a-Service Pattern**
Each agent is implemented as an independent service that can be called synchronously or asynchronously:

```python
# Backend Agent (Python)
class OrderProcessingAgent:
    def __init__(self, mcp_client: MCPClient):
        self.tools = mcp_client.get_tools()
        self.model = "gpt-4"
    
    async def process_message(self, message: str) -> OrderResult:
        # AI processing logic
        pass
```

```typescript
// Frontend Hook (React)
const useAIAgent = ({ distributorId }) => {
    const processMessage = async (content: string) => {
        // Call backend agent or OpenAI directly
        return await openai.chat.completions.create({...});
    };
    
    return { processMessage, isProcessing, lastError };
};
```

### 2. **Model Context Protocol (MCP) Integration**
Agents use MCP for standardized tool access and context management:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["@supabase/mcp-server"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_ANON_KEY": "your-anon-key"
      }
    }
  }
}
```

### 3. **Multi-Tenant Security Architecture**
Each agent respects tenant boundaries through Row-Level Security (RLS):

```sql
-- Ensures agents can only access their tenant's data
CREATE POLICY messages_tenant_isolation ON messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM conversations conv 
            WHERE conv.id = messages.conversation_id 
            AND conv.distributor_id = get_current_distributor_id()
        )
    );
```

## Agent Types and Responsibilities

### 1. **Message Processing Agent**

**Location**: `app/messages/hooks/useAIAgent.ts`

**Purpose**: Analyzes incoming customer messages for intent, sentiment, and actionable items.

**Key Functions**:
- **Intent Detection**: Identifies order requests, support inquiries, complaints
- **Entity Extraction**: Pulls out products, quantities, dates, contact information
- **Sentiment Analysis**: Determines customer mood and urgency level
- **Context Awareness**: Maintains conversation history and customer profile

**Data Flow**:
```
Customer Message → Intent Detection → Entity Extraction → Context Analysis → Structured Output
```

**Database Integration**:
- Reads from: `messages`, `conversations`, `customers`
- Writes to: `ai_responses`, `ai_usage_metrics`

### 2. **Order Processing Agent**

**Location**: `agent-platform/` (Python backend)

**Purpose**: Converts natural language order requests into structured order data.

**Key Functions**:
- **Product Matching**: Maps customer descriptions to product catalog
- **Quantity Extraction**: Identifies quantities and units
- **Order Validation**: Checks inventory, pricing, and business rules
- **Order Creation**: Generates complete order records

**Data Flow**:
```
Natural Language → Product Matching → Quantity Extraction → Validation → Order Creation
```

**Database Integration**:
- Reads from: `products`, `customers`, `orders`
- Writes to: `orders`, `order_products`, `ai_responses`

### 3. **Customer Service Agent**

**Location**: `app/messages/components/AIAssistantPanel.tsx`

**Purpose**: Provides intelligent customer support through automated responses and suggestions.

**Key Functions**:
- **Response Generation**: Creates contextual replies to customer messages
- **Escalation Detection**: Identifies when human intervention is needed
- **Knowledge Base Integration**: Pulls relevant information from documentation
- **Conversation Routing**: Directs conversations to appropriate departments

**Data Flow**:
```
Customer Query → Knowledge Search → Response Generation → Human Review → Delivery
```

**Database Integration**:
- Reads from: `message_templates`, `ai_training_data`, `customers`
- Writes to: `messages`, `ai_responses`

### 4. **Analytics Agent**

**Location**: Database views and scheduled functions

**Purpose**: Provides business intelligence and performance monitoring.

**Key Functions**:
- **Usage Analytics**: Tracks AI system performance and costs
- **Customer Insights**: Analyzes conversation patterns and satisfaction
- **Business Metrics**: Generates reports on order processing efficiency
- **Anomaly Detection**: Identifies unusual patterns requiring attention

**Data Flow**:
```
Raw Data → Aggregation → Analysis → Insights → Dashboards
```

**Database Integration**:
- Reads from: All tables
- Writes to: `ai_usage_metrics`, `ai_model_performance`

## Technology Stack

### Backend Agent Platform
- **Language**: Python 3.11+
- **Framework**: Pydantic AI for agent orchestration
- **AI Models**: OpenAI GPT-4, GPT-3.5-turbo
- **Tools**: MCP (Model Context Protocol) for tool integration
- **Database**: Supabase PostgreSQL with real-time subscriptions

### Frontend AI Integration
- **Language**: TypeScript
- **Framework**: React with Next.js 14
- **State Management**: React hooks and context
- **Real-time**: WebSocket connections
- **UI Components**: Custom components with Tailwind CSS

### Database and Storage
- **Primary DB**: Supabase PostgreSQL
- **Real-time**: Supabase Realtime subscriptions
- **Security**: Row-Level Security (RLS) policies
- **Monitoring**: Custom metrics and alerting

## Communication Patterns

### 1. **Synchronous Processing**
For immediate responses (< 3 seconds):
```typescript
const result = await aiAgent.processMessage(message);
// Immediate UI update
```

### 2. **Asynchronous Processing**
For complex analysis (> 3 seconds):
```typescript
const taskId = await aiAgent.queueAnalysis(conversation);
// WebSocket updates as processing completes
```

### 3. **Real-time Updates**
For live collaboration:
```typescript
supabase
  .channel('ai_responses')
  .on('postgres_changes', { event: 'INSERT' }, (payload) => {
    updateUI(payload.new);
  })
  .subscribe();
```

## Performance Considerations

### 1. **Caching Strategy**
- **Message Analysis**: Cache results for 1 hour
- **Product Matching**: Cache for 24 hours
- **Customer Profiles**: Cache for 6 hours

### 2. **Cost Optimization**
- **Model Selection**: Use GPT-3.5-turbo for simple tasks, GPT-4 for complex analysis
- **Batch Processing**: Group similar requests to reduce API calls
- **Response Streaming**: Stream responses for better user experience

### 3. **Scalability**
- **Horizontal Scaling**: Stateless agents can be deployed across multiple instances
- **Load Balancing**: Distribute requests based on agent type and complexity
- **Database Optimization**: Proper indexing and query optimization

## Security Architecture

### 1. **Multi-Tenant Isolation**
Each agent operation is scoped to a specific distributor:
```python
async def process_order(self, distributor_id: str, message: str):
    # Set tenant context
    await self.supabase.rpc('set_distributor_context', {'distributor_uuid': distributor_id})
    
    # All subsequent operations are automatically scoped
    products = await self.supabase.table('products').select('*').execute()
```

### 2. **PII Protection**
- **Data Masking**: Sensitive information is masked in logs
- **Encryption**: All data encrypted in transit and at rest
- **Access Control**: Role-based permissions for different agent types

### 3. **Audit Logging**
All agent operations are logged for compliance:
```sql
INSERT INTO ai_usage_metrics (
    distributor_id, agent_type, operation, 
    input_tokens, output_tokens, cost_usd, 
    processing_time_ms, created_at
) VALUES (...);
```

## Error Handling and Resilience

### 1. **Graceful Degradation**
Agents fail gracefully when AI services are unavailable:
```typescript
try {
    const aiResult = await processWithAI(message);
    return aiResult;
} catch (error) {
    // Fall back to rule-based processing
    return processWithRules(message);
}
```

### 2. **Retry Logic**
Exponential backoff for API failures:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_openai_api(self, prompt: str):
    # API call with automatic retry
    pass
```

### 3. **Circuit Breaker Pattern**
Prevent cascading failures:
```typescript
if (errorRate > 0.5) {
    // Stop making AI calls, use fallback
    return fallbackResponse;
}
```

## Monitoring and Observability

### 1. **Performance Metrics**
- Response time per agent type
- Success/failure rates
- Cost per operation
- Resource utilization

### 2. **Business Metrics**
- Order conversion rates
- Customer satisfaction scores
- Agent effectiveness metrics
- Cost per conversation

### 3. **Alerting**
- High error rates
- Unusual cost spikes
- Performance degradation
- Security events

## Integration Points

### 1. **External APIs**
- **OpenAI**: Primary AI processing
- **WhatsApp Business**: Message delivery
- **Context7**: Knowledge base access
- **Supabase**: Database and real-time

### 2. **Internal Services**
- **Authentication**: User and tenant management
- **Billing**: Usage tracking and invoicing
- **Notifications**: Alerts and updates
- **Analytics**: Business intelligence

### 3. **Third-party Tools**
- **Monitoring**: Application performance monitoring
- **Logging**: Centralized log aggregation
- **Security**: Vulnerability scanning
- **Backup**: Data backup and recovery

## Future Enhancements

### 1. **Advanced AI Features**
- Multi-modal processing (text, images, audio)
- Custom model fine-tuning
- Advanced reasoning capabilities
- Automated workflow creation

### 2. **Scalability Improvements**
- Kubernetes deployment
- Auto-scaling based on load
- Geographic distribution
- Edge computing integration

### 3. **Business Intelligence**
- Predictive analytics
- Automated reporting
- Custom dashboards
- Advanced data visualization

---

*This architecture supports the current requirements while providing a foundation for future growth and enhancement.*