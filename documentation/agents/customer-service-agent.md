# Customer Service Agent

## Overview

The Customer Service Agent provides intelligent customer support through automated response generation, conversation management, and escalation handling. It leverages customer history, product knowledge, and business context to deliver personalized, accurate customer service across all communication channels.

## Location and Implementation

### Primary Implementation
- **Frontend Hook**: `app/messages/hooks/useAIAgent.ts`
- **UI Component**: `app/messages/components/AIAssistantPanel.tsx`
- **Backend Integration**: `agent-platform/agent_template.py`
- **Type**: Frontend-driven with backend AI processing

### Supporting Components
- **Message Templates**: Database-driven response templates
- **Customer Insights**: Real-time customer profiling
- **Escalation Management**: Automated human handoff
- **Knowledge Base**: Integration with documentation and policies

## Core Functionality

### 1. **Response Generation Pipeline**

The agent generates contextual responses through a multi-stage process:

```typescript
const generateResponseSuggestions = async (
    message: string,
    conversationContext: ConversationContext,
    customerProfile: CustomerProfile
): Promise<ResponseSuggestion[]> => {
    // Step 1: Context Analysis
    const context = await analyzeConversationContext(conversationContext);
    
    // Step 2: Intent Understanding
    const intent = await determineCustomerIntent(message, context);
    
    // Step 3: Knowledge Retrieval
    const relevantInfo = await retrieveRelevantKnowledge(intent, customerProfile);
    
    // Step 4: Response Generation
    const responses = await generateContextualResponses(message, context, relevantInfo);
    
    // Step 5: Response Ranking
    const rankedResponses = await rankResponsesByRelevance(responses, context);
    
    return rankedResponses;
};
```

### 2. **Conversation Context Analysis**

Analyzes conversation history to understand the current situation:

```typescript
interface ConversationContext {
    conversation_id: string;
    customer_id: string;
    message_history: Message[];
    current_intent: string;
    sentiment_trend: SentimentTrend;
    unresolved_issues: Issue[];
    customer_satisfaction: number;
    escalation_signals: EscalationSignal[];
}

const analyzeConversationContext = async (
    conversationContext: ConversationContext
): Promise<ContextAnalysis> => {
    const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
            {
                role: "system",
                content: `Analyze this customer conversation to understand:
                - Current customer needs and intent
                - Emotional state and satisfaction level
                - Unresolved issues or concerns
                - Escalation signals requiring human intervention
                - Conversation context and history patterns`
            },
            {
                role: "user",
                content: `Conversation History: ${JSON.stringify(conversationContext.message_history)}`
            }
        ],
        response_format: { type: "json_object" }
    });
    
    return JSON.parse(response.choices[0].message.content);
};
```

### 3. **Customer Profiling and Insights**

Builds comprehensive customer profiles for personalized service:

```typescript
interface CustomerProfile {
    customer_id: string;
    business_info: {
        name: string;
        industry: string;
        size: string;
        vip_status: boolean;
    };
    order_history: {
        total_orders: number;
        avg_order_value: number;
        preferred_products: string[];
        order_frequency: string;
        last_order_date: string;
    };
    communication_preferences: {
        preferred_channel: string;
        response_time_expectation: string;
        communication_style: string;
    };
    support_history: {
        previous_issues: Issue[];
        satisfaction_scores: number[];
        escalation_history: EscalationEvent[];
    };
    risk_factors: {
        churn_risk: number;
        payment_risk: number;
        satisfaction_risk: number;
    };
}

const analyzeCustomerConversation = async (
    customerId: string,
    conversationHistory: Message[]
): Promise<CustomerInsights> => {
    // Get customer data from database
    const customerData = await getCustomerProfile(customerId);
    
    // Analyze conversation patterns
    const conversationInsights = await analyzeConversationPatterns(conversationHistory);
    
    // Generate insights
    const insights = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
            {
                role: "system",
                content: `Generate customer insights based on profile and conversation history.
                Focus on:
                - Customer satisfaction indicators
                - Potential upselling opportunities
                - Risk factors (churn, payment, satisfaction)
                - Recommended actions for customer success`
            },
            {
                role: "user",
                content: `Customer Profile: ${JSON.stringify(customerData)}
                Conversation History: ${JSON.stringify(conversationHistory)}`
            }
        ],
        response_format: { type: "json_object" }
    });
    
    return JSON.parse(insights.choices[0].message.content);
};
```

### 4. **Knowledge Base Integration**

Integrates with company knowledge base for accurate information:

```typescript
interface KnowledgeBase {
    product_information: ProductInfo[];
    policies: Policy[];
    procedures: Procedure[];
    faqs: FAQ[];
    troubleshooting: TroubleshootingGuide[];
}

const retrieveRelevantKnowledge = async (
    intent: string,
    customerProfile: CustomerProfile
): Promise<RelevantKnowledge> => {
    const searchQueries = generateSearchQueries(intent, customerProfile);
    
    const knowledgeResults = await Promise.all([
        searchProductInformation(searchQueries.product_query),
        searchPolicies(searchQueries.policy_query),
        searchFAQs(searchQueries.faq_query),
        searchTroubleshooting(searchQueries.troubleshooting_query)
    ]);
    
    return {
        product_info: knowledgeResults[0],
        applicable_policies: knowledgeResults[1],
        relevant_faqs: knowledgeResults[2],
        troubleshooting_steps: knowledgeResults[3]
    };
};
```

### 5. **Response Generation and Templating**

Generates personalized responses using templates and AI:

```typescript
interface ResponseTemplate {
    id: string;
    category: string;
    intent: string;
    template: string;
    variables: TemplateVariable[];
    tone: 'PROFESSIONAL' | 'FRIENDLY' | 'EMPATHETIC' | 'URGENT';
    approval_required: boolean;
}

const generateContextualResponses = async (
    message: string,
    context: ContextAnalysis,
    knowledgeBase: RelevantKnowledge
): Promise<ResponseSuggestion[]> => {
    // Get relevant templates
    const templates = await getTemplatesForIntent(context.intent);
    
    // Generate AI responses
    const aiResponses = await generateAIResponses(message, context, knowledgeBase);
    
    // Combine template-based and AI-generated responses
    const allResponses = [...templates, ...aiResponses];
    
    // Personalize responses
    const personalizedResponses = await personalizeResponses(allResponses, context);
    
    return personalizedResponses;
};

const generateAIResponses = async (
    message: string,
    context: ContextAnalysis,
    knowledgeBase: RelevantKnowledge
): Promise<ResponseSuggestion[]> => {
    const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
            {
                role: "system",
                content: `You are a professional customer service representative.
                Generate helpful, accurate, and empathetic responses.
                
                Context: ${JSON.stringify(context)}
                Knowledge Base: ${JSON.stringify(knowledgeBase)}
                
                Generate 3 different response options:
                1. A direct, professional response
                2. A friendly, conversational response  
                3. An empathetic, understanding response
                
                Include specific information from the knowledge base when relevant.`
            },
            {
                role: "user",
                content: `Customer Message: "${message}"`
            }
        ],
        response_format: { type: "json_object" }
    });
    
    return JSON.parse(response.choices[0].message.content).responses;
};
```

### 6. **Escalation Management**

Automatically detects when human intervention is needed:

```typescript
interface EscalationSignal {
    type: 'SENTIMENT' | 'COMPLEXITY' | 'VIP' | 'REPEATED_ISSUE' | 'POLICY_EXCEPTION';
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    description: string;
    suggested_action: string;
    timeout_minutes: number;
}

const detectEscalationSignals = async (
    conversationContext: ConversationContext,
    customerProfile: CustomerProfile
): Promise<EscalationSignal[]> => {
    const signals: EscalationSignal[] = [];
    
    // Check sentiment trends
    if (conversationContext.sentiment_trend.current_sentiment === 'NEGATIVE' && 
        conversationContext.sentiment_trend.severity > 0.7) {
        signals.push({
            type: 'SENTIMENT',
            severity: 'HIGH',
            description: 'Customer sentiment is strongly negative',
            suggested_action: 'Immediate human intervention required',
            timeout_minutes: 5
        });
    }
    
    // Check VIP status
    if (customerProfile.business_info.vip_status) {
        signals.push({
            type: 'VIP',
            severity: 'MEDIUM',
            description: 'VIP customer requires priority handling',
            suggested_action: 'Route to senior support representative',
            timeout_minutes: 10
        });
    }
    
    // Check for repeated issues
    const repeatedIssues = identifyRepeatedIssues(conversationContext);
    if (repeatedIssues.length > 0) {
        signals.push({
            type: 'REPEATED_ISSUE',
            severity: 'HIGH',
            description: 'Customer has experienced this issue before',
            suggested_action: 'Escalate to technical specialist',
            timeout_minutes: 15
        });
    }
    
    return signals;
};
```

## Database Integration

### Message Templates Management

```sql
-- Get templates for specific intent
SELECT mt.*, d.business_name
FROM message_templates mt
JOIN distributors d ON d.id = mt.distributor_id
WHERE mt.intent = $1 
  AND mt.distributor_id = $2 
  AND mt.is_active = true
ORDER BY mt.usage_count DESC;

-- Track template usage
UPDATE message_templates 
SET usage_count = usage_count + 1,
    last_used_at = NOW()
WHERE id = $1;

-- Store AI-generated responses for future training
INSERT INTO ai_responses (
    message_id, agent_type, request_type, response_data,
    confidence_score, processing_time_ms, tokens_used,
    cost_usd, model_used, created_at
) VALUES (
    $1, 'customer_service', 'response_generation', $2,
    $3, $4, $5, $6, $7, NOW()
);
```

### Customer Insights Storage

```sql
-- Store customer insights
INSERT INTO customer_insights (
    customer_id, insight_type, insight_data, 
    confidence_score, generated_at, expires_at
) VALUES (
    $1, 'satisfaction_analysis', $2, $3, NOW(), NOW() + INTERVAL '7 days'
);

-- Get customer support history
SELECT c.*, 
       COUNT(conv.id) as total_conversations,
       AVG(CASE WHEN m.ai_confidence IS NOT NULL THEN m.ai_confidence END) as avg_ai_confidence,
       COUNT(CASE WHEN conv.status = 'ESCALATED' THEN 1 END) as escalation_count
FROM customers c
LEFT JOIN conversations conv ON conv.customer_id = c.id
LEFT JOIN messages m ON m.conversation_id = conv.id
WHERE c.id = $1 AND c.distributor_id = $2
GROUP BY c.id;
```

## User Interface Integration

### AI Assistant Panel

The main UI component that displays AI-powered customer service features:

```typescript
const AIAssistantPanel = ({ 
    conversationId, 
    conversation, 
    messages,
    onSendSuggestion,
    onCreateOrder,
    onViewCustomerOrders 
}: AIAssistantPanelProps) => {
    const [customerInsights, setCustomerInsights] = useState<CustomerInsights | null>(null);
    const [responseSuggestions, setResponseSuggestions] = useState<ResponseSuggestion[]>([]);
    const [escalationSignals, setEscalationSignals] = useState<EscalationSignal[]>([]);
    
    // Generate customer insights
    useEffect(() => {
        if (conversation && messages.length > 0) {
            analyzeCustomerConversation(conversation.customerId, messages)
                .then(setCustomerInsights);
        }
    }, [conversation, messages]);
    
    // Generate response suggestions
    useEffect(() => {
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.isFromCustomer) {
                generateResponseSuggestions(lastMessage.content, conversationContext, customerProfile)
                    .then(setResponseSuggestions);
            }
        }
    }, [messages]);
    
    return (
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            {/* Customer Insights Section */}
            <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Customer Insights
                </h3>
                
                {customerInsights && (
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
                            <span className="text-sm text-gray-600">Order Value</span>
                            <span className="text-sm font-medium">
                                ${customerInsights.avg_order_value.toFixed(2)}
                            </span>
                        </div>
                        
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Total Orders</span>
                            <span className="text-sm font-medium">
                                {customerInsights.total_orders}
                            </span>
                        </div>
                    </div>
                )}
            </div>
            
            {/* Escalation Alerts */}
            {escalationSignals.length > 0 && (
                <div className="p-4 border-b border-gray-200 bg-red-50">
                    <h4 className="text-sm font-semibold text-red-900 mb-2">
                        Escalation Required
                    </h4>
                    {escalationSignals.map((signal, index) => (
                        <div key={index} className="text-sm text-red-700 mb-1">
                            {signal.description}
                        </div>
                    ))}
                    <button className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm">
                        Escalate to Human
                    </button>
                </div>
            )}
            
            {/* Response Suggestions */}
            <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Suggested Responses
                </h3>
                
                <div className="space-y-2">
                    {responseSuggestions.map((suggestion, index) => (
                        <button
                            key={index}
                            onClick={() => onSendSuggestion(suggestion.content)}
                            className="w-full text-left p-3 rounded border border-gray-200 hover:bg-gray-50 text-sm"
                        >
                            <div className="font-medium text-gray-900 mb-1">
                                {suggestion.title}
                            </div>
                            <div className="text-gray-600 line-clamp-2">
                                {suggestion.preview}
                            </div>
                            <div className="flex items-center justify-between mt-2">
                                <span className="text-xs text-gray-500">
                                    {suggestion.tone}
                                </span>
                                <span className="text-xs text-gray-500">
                                    {(suggestion.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                        </button>
                    ))}
                </div>
            </div>
            
            {/* Quick Actions */}
            <div className="p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Quick Actions
                </h3>
                
                <div className="space-y-2">
                    <button
                        onClick={onCreateOrder}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                    >
                        Create Order
                    </button>
                    
                    <button
                        onClick={onViewCustomerOrders}
                        className="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
                    >
                        View Order History
                    </button>
                </div>
            </div>
        </div>
    );
};
```

## Performance Optimization

### Response Caching
```typescript
const responseCacheKey = (message: string, customerId: string) => 
    `response_${customerId}_${btoa(message).slice(0, 20)}`;

const getCachedResponse = async (cacheKey: string): Promise<ResponseSuggestion[] | null> => {
    const cached = await redis.get(cacheKey);
    return cached ? JSON.parse(cached) : null;
};

const cacheResponse = async (cacheKey: string, responses: ResponseSuggestion[]) => {
    await redis.setex(cacheKey, 3600, JSON.stringify(responses)); // Cache for 1 hour
};
```

### Async Processing
```typescript
const processInBackground = async (conversationId: string) => {
    // Queue background analysis
    await queue.add('analyze_conversation', {
        conversationId,
        priority: 'normal'
    });
    
    // Return immediately, update UI when complete
    return { status: 'processing', estimatedTime: 5000 };
};
```

## Quality Assurance

### Response Quality Scoring
```typescript
const scoreResponseQuality = async (
    originalMessage: string,
    generatedResponse: string,
    customerProfile: CustomerProfile
): Promise<QualityScore> => {
    const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
            {
                role: "system",
                content: `Rate the quality of this customer service response on a scale of 1-10:
                - Accuracy: Does it answer the customer's question?
                - Tone: Is it appropriate for the customer and situation?
                - Helpfulness: Does it provide useful information?
                - Completeness: Are all aspects of the question addressed?`
            },
            {
                role: "user",
                content: `Customer Message: "${originalMessage}"
                Agent Response: "${generatedResponse}"
                Customer Profile: ${JSON.stringify(customerProfile)}`
            }
        ],
        response_format: { type: "json_object" }
    });
    
    return JSON.parse(response.choices[0].message.content);
};
```

### A/B Testing
```typescript
const runResponseABTest = async (
    message: string,
    context: ConversationContext
): Promise<ABTestResult> => {
    const [responseA, responseB] = await Promise.all([
        generateResponse(message, context, { model: 'gpt-4' }),
        generateResponse(message, context, { model: 'gpt-3.5-turbo' })
    ]);
    
    // Track which response is used
    const selectedResponse = Math.random() > 0.5 ? responseA : responseB;
    
    await logABTest({
        message_id: context.messageId,
        variant: selectedResponse === responseA ? 'A' : 'B',
        response: selectedResponse
    });
    
    return selectedResponse;
};
```

## Monitoring and Analytics

### Customer Satisfaction Metrics
```sql
-- Customer satisfaction trends
SELECT 
    DATE_TRUNC('week', created_at) as week,
    AVG(satisfaction_score) as avg_satisfaction,
    COUNT(*) as total_interactions,
    COUNT(*) FILTER (WHERE escalated = true) as escalation_count
FROM customer_interactions
WHERE distributor_id = $1
GROUP BY week
ORDER BY week DESC;

-- Agent performance metrics
SELECT 
    agent_type,
    AVG(response_time_ms) as avg_response_time,
    AVG(confidence_score) as avg_confidence,
    COUNT(*) as total_responses,
    COUNT(*) FILTER (WHERE human_review_required = true) as review_required_count
FROM ai_responses
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY agent_type;
```

### Cost Analytics
```sql
-- AI usage costs by agent type
SELECT 
    agent_type,
    SUM(cost_usd) as total_cost,
    COUNT(*) as total_requests,
    AVG(cost_usd) as avg_cost_per_request,
    SUM(tokens_used) as total_tokens
FROM ai_responses
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY agent_type;
```

## Future Enhancements

### Advanced Features
1. **Multi-language Support**: Respond in customer's preferred language
2. **Voice Integration**: Handle voice messages and calls
3. **Video Support**: Analyze video messages for context
4. **Emotional Intelligence**: Advanced emotion detection and response
5. **Predictive Support**: Anticipate customer needs before they ask

### Integration Improvements
1. **CRM Integration**: Sync with external CRM systems
2. **Social Media**: Handle social media customer service
3. **Live Chat**: Seamless handoff between AI and human agents
4. **Mobile App**: Native mobile customer service experience
5. **API Ecosystem**: Third-party integrations and plugins

---

*The Customer Service Agent enhances customer experience through intelligent automation while maintaining the human touch when needed, ensuring high satisfaction and efficient problem resolution.*