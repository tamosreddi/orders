# Message Processing Agent

## Overview

The Message Processing Agent is the core intelligence component responsible for analyzing and understanding customer messages across all communication channels (WhatsApp, SMS, Email). It serves as the first line of AI processing, extracting meaning, intent, and actionable information from natural language communications.

## Location and Implementation

### Primary Implementation
- **File**: `app/messages/hooks/useAIAgent.ts`
- **Type**: React Hook with OpenAI integration
- **Runtime**: Frontend (Next.js)
- **Dependencies**: OpenAI API, Supabase client

### Supporting Components
- **UI Component**: `app/messages/components/AIAssistantPanel.tsx`
- **Message Display**: `app/messages/components/MessageThread.tsx`
- **Data Types**: `app/messages/types/message.ts`

## Core Functionality

### 1. **Message Analysis Pipeline**

The agent processes each message through a structured pipeline:

```typescript
const processMessage = async (content: string, context: ConversationContext) => {
    // Step 1: Intent Detection
    const intent = await detectIntent(content);
    
    // Step 2: Entity Extraction
    const entities = await extractEntities(content);
    
    // Step 3: Sentiment Analysis
    const sentiment = await analyzeSentiment(content);
    
    // Step 4: Context Integration
    const enrichedResult = await integrateContext(intent, entities, sentiment, context);
    
    return enrichedResult;
};
```

### 2. **Intent Detection**

Identifies the primary purpose of each message:

**Supported Intents**:
- `ORDER_REQUEST` - Customer wants to place an order
- `ORDER_INQUIRY` - Questions about existing orders
- `PRODUCT_INQUIRY` - Questions about products or catalog
- `SUPPORT_REQUEST` - Technical or service support needed
- `COMPLAINT` - Customer complaint or issue
- `COMPLIMENT` - Positive feedback
- `GENERAL_INQUIRY` - General questions
- `CANCELLATION` - Order cancellation request
- `MODIFICATION` - Order modification request

**Implementation**:
```typescript
const detectIntent = async (message: string): Promise<MessageIntent> => {
    const response = await openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [
            {
                role: "system",
                content: `Analyze this customer message and determine the primary intent.
                Return one of: ORDER_REQUEST, ORDER_INQUIRY, PRODUCT_INQUIRY, 
                SUPPORT_REQUEST, COMPLAINT, COMPLIMENT, GENERAL_INQUIRY, 
                CANCELLATION, MODIFICATION`
            },
            {
                role: "user",
                content: message
            }
        ],
        max_tokens: 50
    });
    
    return response.choices[0].message.content as MessageIntent;
};
```

### 3. **Entity Extraction**

Extracts structured information from natural language:

**Extracted Entities**:
- **Products**: Product names, SKUs, descriptions
- **Quantities**: Numbers, units, measurements
- **Dates**: Delivery dates, order dates, deadlines
- **Contact Information**: Names, addresses, phone numbers
- **Monetary Values**: Prices, budgets, payments
- **Location Information**: Addresses, delivery locations

**Implementation**:
```typescript
interface ExtractedEntities {
    products: ProductEntity[];
    quantities: QuantityEntity[];
    dates: DateEntity[];
    contacts: ContactEntity[];
    monetary: MonetaryEntity[];
    locations: LocationEntity[];
}

const extractEntities = async (message: string): Promise<ExtractedEntities> => {
    const response = await openai.chat.completions.create({
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
                content: message
            }
        ],
        response_format: { type: "json_object" }
    });
    
    return JSON.parse(response.choices[0].message.content);
};
```

### 4. **Sentiment Analysis**

Determines customer emotional state and urgency:

**Sentiment Categories**:
- `POSITIVE` - Happy, satisfied customer
- `NEUTRAL` - Neutral or informational tone
- `NEGATIVE` - Frustrated or dissatisfied
- `URGENT` - Time-sensitive or emergency
- `CONFUSED` - Customer needs clarification

**Confidence Scoring**:
- Each sentiment includes a confidence score (0.0 to 1.0)
- Scores below 0.7 trigger human review
- Urgent messages automatically escalate

```typescript
interface SentimentResult {
    sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE' | 'URGENT' | 'CONFUSED';
    confidence: number;
    emotional_indicators: string[];
    urgency_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}
```

### 5. **Context Integration**

Combines message analysis with conversation history and customer profile:

**Context Sources**:
- **Previous Messages**: Last 10 messages in conversation
- **Customer Profile**: Order history, preferences, VIP status
- **Product Catalog**: Available products and pricing
- **Business Rules**: Policies, availability, restrictions

```typescript
const integrateContext = async (
    intent: MessageIntent,
    entities: ExtractedEntities,
    sentiment: SentimentResult,
    context: ConversationContext
): Promise<ProcessedMessage> => {
    // Combine with conversation history
    const conversationContext = await buildConversationContext(context.messages);
    
    // Add customer profile
    const customerProfile = await getCustomerProfile(context.customerId);
    
    // Check product availability
    const productValidation = await validateProducts(entities.products);
    
    // Generate actionable insights
    const insights = await generateInsights(intent, entities, sentiment, {
        conversation: conversationContext,
        customer: customerProfile,
        products: productValidation
    });
    
    return {
        original_message: context.content,
        intent,
        entities,
        sentiment,
        insights,
        confidence: calculateOverallConfidence(intent, entities, sentiment),
        suggested_actions: generateSuggestedActions(insights),
        requires_human_review: shouldRequireHumanReview(sentiment, insights)
    };
};
```

## Database Integration

### Data Read Operations

The agent reads from multiple tables to build context:

```sql
-- Get conversation history
SELECT m.content, m.is_from_customer, m.created_at
FROM messages m
JOIN conversations c ON c.id = m.conversation_id
WHERE c.id = $1 AND c.distributor_id = $2
ORDER BY m.created_at DESC
LIMIT 10;

-- Get customer profile
SELECT c.*, COUNT(o.id) as order_count, AVG(o.total_amount) as avg_order_value
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE c.id = $1 AND c.distributor_id = $2
GROUP BY c.id;

-- Get product catalog
SELECT p.*, COUNT(op.id) as order_frequency
FROM products p
LEFT JOIN order_products op ON op.product_id = p.id
WHERE p.distributor_id = $1 AND p.status = 'ACTIVE'
GROUP BY p.id
ORDER BY order_frequency DESC;
```

### Data Write Operations

Results are stored for future reference and analysis:

```sql
-- Store AI analysis results
INSERT INTO ai_responses (
    message_id, agent_type, request_type, response_data,
    confidence_score, processing_time_ms, tokens_used,
    cost_usd, model_used, created_at
) VALUES (
    $1, 'message_processor', 'full_analysis', $2,
    $3, $4, $5, $6, $7, NOW()
);

-- Update message with AI insights
UPDATE messages SET
    ai_processed = true,
    ai_confidence = $2,
    ai_extracted_intent = $3,
    ai_extracted_products = $4,
    ai_suggested_responses = $5,
    updated_at = NOW()
WHERE id = $1;
```

## Performance Characteristics

### Response Times
- **Simple Intent Detection**: < 500ms
- **Full Entity Extraction**: < 1.5s
- **Complex Context Analysis**: < 3s
- **Batch Processing**: 100 messages/minute

### Token Usage
- **Intent Detection**: ~100 tokens per message
- **Entity Extraction**: ~300 tokens per message
- **Context Integration**: ~500 tokens per message
- **Total Average**: ~900 tokens per message

### Cost Estimates (GPT-4)
- **Per Message**: $0.015 - $0.025
- **Per Conversation**: $0.10 - $0.20
- **Monthly (1000 messages)**: $15 - $25

## Error Handling

### Graceful Degradation
When AI services are unavailable:

```typescript
const fallbackProcessing = (message: string): ProcessedMessage => {
    // Rule-based intent detection
    const intent = detectIntentWithRules(message);
    
    // Keyword-based entity extraction
    const entities = extractEntitiesWithKeywords(message);
    
    // Simple sentiment analysis
    const sentiment = analyzeSentimentWithRules(message);
    
    return {
        original_message: message,
        intent,
        entities,
        sentiment,
        confidence: 0.6, // Lower confidence for rule-based
        fallback_used: true,
        requires_human_review: true
    };
};
```

### Retry Logic
Automatic retry with exponential backoff:

```typescript
const processMessageWithRetry = async (message: string, maxRetries = 3) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await processMessage(message);
        } catch (error) {
            if (attempt === maxRetries) {
                // Use fallback processing
                return fallbackProcessing(message);
            }
            
            // Wait before retry (exponential backoff)
            await new Promise(resolve => 
                setTimeout(resolve, Math.pow(2, attempt) * 1000)
            );
        }
    }
};
```

## Quality Assurance

### Confidence Scoring
Each analysis includes confidence metrics:

```typescript
interface ConfidenceMetrics {
    overall: number;           // 0.0 to 1.0
    intent_confidence: number;
    entity_confidence: number;
    sentiment_confidence: number;
    context_alignment: number;
}
```

### Human Review Triggers
Messages requiring human review:
- Overall confidence < 0.7
- Negative sentiment with high urgency
- Complex entity extraction
- Conflicting context signals
- Customer VIP status

### Continuous Learning
The system learns from corrections:

```sql
-- Store training data from corrections
INSERT INTO ai_training_data (
    original_input, ai_output, human_correction,
    correction_type, data_source, created_at
) VALUES (
    $1, $2, $3, 'intent_correction', 'human_review', NOW()
);
```

## Integration with Other Agents

### Order Processing Agent
Passes extracted order information:

```typescript
if (processedMessage.intent === 'ORDER_REQUEST') {
    const orderResult = await orderProcessingAgent.processOrder({
        customerId: conversation.customerId,
        extractedProducts: processedMessage.entities.products,
        extractedQuantities: processedMessage.entities.quantities,
        context: processedMessage.insights
    });
}
```

### Customer Service Agent
Provides context for response generation:

```typescript
const responseContext = {
    customer_sentiment: processedMessage.sentiment,
    conversation_history: processedMessage.insights.conversation,
    customer_profile: processedMessage.insights.customer,
    urgency_level: processedMessage.sentiment.urgency_level
};

const suggestedResponse = await customerServiceAgent.generateResponse(
    processedMessage.original_message,
    responseContext
);
```

## Monitoring and Analytics

### Performance Metrics
- Processing time distribution
- Confidence score trends
- Error rates by message type
- Cost per conversation

### Quality Metrics
- Human review rates
- Correction frequency
- Customer satisfaction correlation
- Intent detection accuracy

### Business Metrics
- Order conversion rates
- Response time improvement
- Customer satisfaction scores
- Cost per successful interaction

## Configuration

### Model Selection
Different models for different tasks:

```typescript
const modelConfig = {
    intent_detection: "gpt-3.5-turbo",    // Fast and cost-effective
    entity_extraction: "gpt-4",           // More accurate
    sentiment_analysis: "gpt-3.5-turbo",  // Sufficient accuracy
    context_integration: "gpt-4"          // Complex reasoning
};
```

### Prompt Templates
Standardized prompts for consistency:

```typescript
const prompts = {
    intent_detection: `
        You are an AI assistant analyzing customer messages for a B2B order management system.
        Determine the primary intent of this message.
        
        Available intents: ORDER_REQUEST, ORDER_INQUIRY, PRODUCT_INQUIRY, 
        SUPPORT_REQUEST, COMPLAINT, COMPLIMENT, GENERAL_INQUIRY, 
        CANCELLATION, MODIFICATION
        
        Message: {message}
        
        Return only the intent name.
    `,
    
    entity_extraction: `
        Extract structured entities from this customer message.
        Focus on products, quantities, dates, and contact information.
        
        Message: {message}
        
        Return a JSON object with the extracted entities.
    `
};
```

## Troubleshooting

### Common Issues

1. **Low Confidence Scores**
   - Review prompt templates
   - Check training data quality
   - Increase context window

2. **High Processing Times**
   - Optimize prompt length
   - Use faster models for simple tasks
   - Implement caching

3. **Incorrect Intent Detection**
   - Analyze failed cases
   - Update training data
   - Refine prompt templates

4. **High API Costs**
   - Optimize token usage
   - Use appropriate model for each task
   - Implement request batching

### Debug Mode
Enable detailed logging:

```typescript
const DEBUG_MODE = process.env.NODE_ENV === 'development';

if (DEBUG_MODE) {
    console.log('Message Processing Debug:', {
        input: message,
        intent: result.intent,
        entities: result.entities,
        confidence: result.confidence,
        processing_time: processingTime,
        tokens_used: tokensUsed
    });
}
```

---

*The Message Processing Agent is the foundation of the AI system, providing intelligent analysis that drives all downstream automation and decision-making processes.*