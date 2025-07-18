# 🛠️ Practical Examples & Use Cases

**Real-world scenarios and code examples for working with the AI-powered order management database**

## 🎯 **Overview**

This guide provides practical examples for common development scenarios. Each example includes:
- **Context**: When you'd use this
- **SQL Query**: Complete working example
- **Expected Output**: What the data looks like
- **Implementation Notes**: Important considerations

---

## 👥 **Customer Management Examples**

### **Example 1: Customer Dashboard with Activity Summary**

**Context**: Building the main customers page with status and recent activity.

```sql
-- Get customers with order statistics and last activity
SELECT 
    c.id,
    c.business_name,
    c.customer_code,
    c.status,
    c.total_orders,
    c.total_spent,
    c.last_ordered_date,
    
    -- Recent activity metrics
    COUNT(DISTINCT CASE WHEN o.created_at >= NOW() - INTERVAL '30 days' THEN o.id END) as orders_last_30_days,
    COUNT(DISTINCT CASE WHEN conv.last_message_at >= NOW() - INTERVAL '7 days' THEN conv.id END) as active_conversations,
    
    -- Labels for display
    ARRAY_AGG(DISTINCT cl.name) FILTER (WHERE cl.name IS NOT NULL) as labels,
    ARRAY_AGG(DISTINCT cl.color) FILTER (WHERE cl.color IS NOT NULL) as label_colors
    
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
LEFT JOIN conversations conv ON conv.customer_id = c.id
LEFT JOIN customer_label_assignments cla ON cla.customer_id = c.id
LEFT JOIN customer_labels cl ON cl.id = cla.label_id
WHERE c.distributor_id = get_current_distributor_id()
GROUP BY c.id, c.business_name, c.customer_code, c.status, c.total_orders, c.total_spent, c.last_ordered_date
ORDER BY c.last_ordered_date DESC NULLS LAST;
```

**Expected Output**:
```json
{
  "id": "uuid",
  "business_name": "Supermarket ABC",
  "customer_code": "SUP001",
  "status": "ORDERING",
  "total_orders": 45,
  "total_spent": 12500.00,
  "last_ordered_date": "2024-07-15",
  "orders_last_30_days": 3,
  "active_conversations": 1,
  "labels": ["Dairy", "Restaurant"],
  "label_colors": ["#FEF3C7", "#E0F2FE"]
}
```

---

### **Example 2: Customer Risk Analysis**

**Context**: Identifying at-risk customers for retention campaigns.

```sql
-- Find customers who haven't ordered recently but were previously active
WITH customer_metrics AS (
    SELECT 
        c.id,
        c.business_name,
        c.last_ordered_date,
        c.total_orders,
        c.total_spent,
        
        -- Calculate days since last order
        EXTRACT(days FROM NOW() - c.last_ordered_date) as days_since_last_order,
        
        -- Average order frequency (orders per month)
        CASE 
            WHEN c.total_orders > 0 AND c.last_ordered_date IS NOT NULL 
            THEN c.total_orders::DECIMAL / GREATEST(EXTRACT(days FROM c.last_ordered_date - c.joined_date) / 30.0, 1)
            ELSE 0 
        END as avg_orders_per_month,
        
        -- Recent message activity
        COUNT(DISTINCT m.id) as messages_last_7_days
        
    FROM customers c
    LEFT JOIN conversations conv ON conv.customer_id = c.id
    LEFT JOIN messages m ON m.conversation_id = conv.id AND m.created_at >= NOW() - INTERVAL '7 days'
    WHERE c.distributor_id = get_current_distributor_id()
    AND c.total_orders > 0  -- Only previously active customers
    GROUP BY c.id, c.business_name, c.last_ordered_date, c.total_orders, c.total_spent, c.joined_date
)
SELECT 
    *,
    CASE 
        WHEN days_since_last_order > 60 AND avg_orders_per_month > 1 THEN 'HIGH_RISK'
        WHEN days_since_last_order > 30 AND avg_orders_per_month > 0.5 THEN 'MEDIUM_RISK'
        WHEN days_since_last_order > 14 AND messages_last_7_days = 0 THEN 'LOW_RISK'
        ELSE 'ACTIVE'
    END as risk_level
FROM customer_metrics
WHERE days_since_last_order > 14  -- Focus on customers with some inactivity
ORDER BY 
    CASE 
        WHEN days_since_last_order > 60 AND avg_orders_per_month > 1 THEN 1
        WHEN days_since_last_order > 30 AND avg_orders_per_month > 0.5 THEN 2
        ELSE 3
    END,
    total_spent DESC;
```

---

## 💬 **Messaging & AI Examples**

### **Example 3: Messages Requiring Human Review**

**Context**: Building a queue for customer service representatives to review AI responses.

```sql
-- Get messages where AI needs human review
SELECT 
    m.id as message_id,
    m.content,
    m.created_at,
    m.is_from_customer,
    
    -- Customer context
    c.business_name,
    c.customer_code,
    conv.channel,
    
    -- AI analysis
    ar.response_content as ai_suggestion,
    ar.confidence,
    ar.agent_type,
    
    -- Order context if any
    o.id as potential_order_id,
    o.total_amount as potential_order_amount,
    
    -- Priority scoring
    CASE 
        WHEN ar.confidence < 0.5 AND m.is_from_customer THEN 'HIGH'
        WHEN ar.confidence < 0.7 AND o.total_amount > 1000 THEN 'HIGH'
        WHEN ar.confidence < 0.8 THEN 'MEDIUM'
        ELSE 'LOW'
    END as review_priority
    
FROM messages m
JOIN conversations conv ON conv.id = m.conversation_id
JOIN customers c ON c.id = conv.customer_id
LEFT JOIN ai_responses ar ON ar.message_id = m.id
LEFT JOIN orders o ON o.ai_source_message_id = m.id
WHERE c.distributor_id = get_current_distributor_id()
AND m.ai_processed = TRUE
AND (
    ar.confidence < 0.8 OR  -- Low confidence responses
    (o.id IS NOT NULL AND o.requires_review = TRUE) OR  -- AI-generated orders needing review
    m.created_at >= NOW() - INTERVAL '24 hours'  -- Recent messages only
)
ORDER BY 
    CASE 
        WHEN ar.confidence < 0.5 AND m.is_from_customer THEN 1
        WHEN ar.confidence < 0.7 AND o.total_amount > 1000 THEN 2
        WHEN ar.confidence < 0.8 THEN 3
        ELSE 4
    END,
    m.created_at DESC;
```

---

### **Example 4: Conversation History with AI Context**

**Context**: Displaying a complete conversation thread with AI insights for customer service.

```sql
-- Get complete conversation with AI context
WITH message_ai_data AS (
    SELECT 
        m.*,
        ar.response_content,
        ar.confidence,
        ar.extracted_data,
        
        -- Check if message led to an order
        CASE WHEN o.id IS NOT NULL THEN TRUE ELSE FALSE END as created_order,
        o.id as order_id,
        o.total_amount
        
    FROM messages m
    LEFT JOIN ai_responses ar ON ar.message_id = m.id AND ar.agent_type = 'ORDER_PROCESSING'
    LEFT JOIN orders o ON o.ai_source_message_id = m.id
    WHERE m.conversation_id = $1  -- Parameter: conversation ID
)
SELECT 
    -- Message details
    mad.id,
    mad.content,
    mad.is_from_customer,
    mad.created_at,
    mad.status,
    
    -- AI analysis
    mad.response_content as ai_suggestion,
    mad.confidence,
    mad.extracted_data,
    mad.created_order,
    mad.order_id,
    mad.total_amount,
    
    -- Customer context (from first message)
    FIRST_VALUE(c.business_name) OVER (ORDER BY mad.created_at) as customer_name,
    FIRST_VALUE(conv.channel) OVER (ORDER BY mad.created_at) as channel
    
FROM message_ai_data mad
JOIN conversations conv ON conv.id = mad.conversation_id
JOIN customers c ON c.id = conv.customer_id
ORDER BY mad.created_at ASC;
```

---

## 📦 **Order Management Examples**

### **Example 5: AI-Generated Orders Dashboard**

**Context**: Monitoring AI order processing performance and accuracy.

```sql
-- AI order processing analytics
SELECT 
    DATE(o.created_at) as order_date,
    
    -- Order counts by source
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE o.ai_generated = TRUE) as ai_generated_orders,
    COUNT(*) FILTER (WHERE o.ai_generated = TRUE AND o.requires_review = FALSE) as auto_approved_orders,
    COUNT(*) FILTER (WHERE o.ai_generated = TRUE AND o.requires_review = TRUE) as review_required_orders,
    
    -- Confidence metrics
    AVG(o.ai_confidence) FILTER (WHERE o.ai_generated = TRUE) as avg_ai_confidence,
    COUNT(*) FILTER (WHERE o.ai_confidence >= 0.8) as high_confidence_orders,
    COUNT(*) FILTER (WHERE o.ai_confidence < 0.5) as low_confidence_orders,
    
    -- Financial impact
    SUM(o.total_amount) as total_order_value,
    SUM(o.total_amount) FILTER (WHERE o.ai_generated = TRUE) as ai_generated_value,
    
    -- Processing efficiency
    ROUND(
        COUNT(*) FILTER (WHERE o.ai_generated = TRUE)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 
        2
    ) as ai_automation_rate
    
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE c.distributor_id = get_current_distributor_id()
AND o.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(o.created_at)
ORDER BY order_date DESC;
```

**Expected Output**:
```json
{
  "order_date": "2024-07-15",
  "total_orders": 25,
  "ai_generated_orders": 18,
  "auto_approved_orders": 12,
  "review_required_orders": 6,
  "avg_ai_confidence": 0.76,
  "high_confidence_orders": 12,
  "low_confidence_orders": 2,
  "total_order_value": 15750.00,
  "ai_generated_value": 11200.00,
  "ai_automation_rate": 72.00
}
```

---

### **Example 6: Order Details with Product Matching**

**Context**: Displaying order details with AI product matching results.

```sql
-- Get order with product line items and AI matching details
SELECT 
    o.id as order_id,
    o.status,
    o.total_amount,
    o.ai_generated,
    o.ai_confidence,
    
    -- Customer info
    c.business_name,
    c.customer_code,
    
    -- Order products with AI matching
    json_agg(
        json_build_object(
            'product_name', op.product_name,
            'quantity', op.quantity,
            'unit_price', op.unit_price,
            'line_price', op.line_price,
            'ai_extracted', op.ai_extracted,
            'ai_original_text', op.ai_original_text,
            'ai_confidence', op.ai_confidence,
            'matched_product_id', op.matched_product_id,
            'matched_product_name', p.name,
            'matching_method', op.matching_method,
            'matching_confidence', op.matching_confidence
        ) ORDER BY op.line_order
    ) as products
    
FROM orders o
JOIN customers c ON c.id = o.customer_id
JOIN order_products op ON op.order_id = o.id
LEFT JOIN products p ON p.id = op.matched_product_id
WHERE o.id = $1  -- Parameter: order ID
AND c.distributor_id = get_current_distributor_id()
GROUP BY o.id, o.status, o.total_amount, o.ai_generated, o.ai_confidence, c.business_name, c.customer_code;
```

---

## 🤖 **AI Performance Examples**

### **Example 7: AI Cost and Usage Analysis**

**Context**: Monitoring AI costs and optimizing usage across different agent types.

```sql
-- AI usage and cost analysis by agent type
WITH daily_usage AS (
    SELECT 
        date,
        agent_type,
        SUM(requests_count) as total_requests,
        SUM(successful_requests) as successful_requests,
        SUM(cost_cents) as cost_cents,
        SUM(total_tokens) as total_tokens,
        AVG(avg_confidence) as avg_confidence,
        AVG(avg_response_time_ms) as avg_response_time
    FROM ai_usage_metrics 
    WHERE distributor_id = get_current_distributor_id()
    AND date >= NOW() - INTERVAL '30 days'
    GROUP BY date, agent_type
),
agent_totals AS (
    SELECT 
        agent_type,
        SUM(total_requests) as total_requests,
        SUM(successful_requests) as successful_requests,
        SUM(cost_cents) as total_cost_cents,
        SUM(total_tokens) as total_tokens,
        AVG(avg_confidence) as avg_confidence,
        AVG(avg_response_time) as avg_response_time,
        
        -- Calculate efficiency metrics
        ROUND(SUM(successful_requests)::DECIMAL / NULLIF(SUM(total_requests), 0) * 100, 2) as success_rate,
        ROUND(SUM(cost_cents)::DECIMAL / NULLIF(SUM(successful_requests), 0), 4) as cost_per_success_cents,
        ROUND(SUM(total_tokens)::DECIMAL / NULLIF(SUM(total_requests), 0), 0) as avg_tokens_per_request
    FROM daily_usage
    GROUP BY agent_type
)
SELECT 
    agent_type,
    total_requests,
    successful_requests,
    total_cost_cents / 100.0 as total_cost_usd,
    total_tokens,
    avg_confidence,
    avg_response_time,
    success_rate,
    cost_per_success_cents / 100.0 as cost_per_success_usd,
    avg_tokens_per_request
FROM agent_totals
ORDER BY total_cost_cents DESC;
```

---

### **Example 8: AI Training Data Collection**

**Context**: Identifying poor AI responses that need to become training data.

```sql
-- Find AI responses that need to become training data
SELECT 
    ar.id as response_id,
    ar.response_content,
    ar.confidence,
    ar.human_feedback,
    
    -- Original message context
    m.content as original_message,
    m.created_at as message_time,
    
    -- Customer context
    c.business_name,
    
    -- Current extracted data (what AI thought)
    ar.extracted_data as ai_interpretation,
    
    -- Actual order data (what really happened)
    json_build_object(
        'order_id', o.id,
        'total_amount', o.total_amount,
        'products', (
            SELECT json_agg(
                json_build_object(
                    'name', op.product_name,
                    'quantity', op.quantity,
                    'unit_price', op.unit_price
                )
            )
            FROM order_products op 
            WHERE op.order_id = o.id
        )
    ) as actual_order_data
    
FROM ai_responses ar
JOIN messages m ON m.id = ar.message_id
JOIN conversations conv ON conv.id = m.conversation_id
JOIN customers c ON c.id = conv.customer_id
LEFT JOIN orders o ON o.ai_source_message_id = m.id
WHERE c.distributor_id = get_current_distributor_id()
AND ar.agent_type = 'ORDER_PROCESSING'
AND (
    ar.human_feedback = 'NOT_HELPFUL' OR
    ar.confidence < 0.6 OR
    (o.id IS NOT NULL AND ar.extracted_data IS DISTINCT FROM 
        (SELECT json_build_object('products', json_agg(json_build_object('name', op.product_name, 'quantity', op.quantity)))
         FROM order_products op WHERE op.order_id = o.id)
    )
)
ORDER BY ar.created_at DESC
LIMIT 50;
```

---

## 🔗 **Integration Examples**

### **Example 9: Webhook Event Processing**

**Context**: Processing incoming webhook events and updating related records.

```sql
-- Process webhook delivery results and update integration status
WITH webhook_stats AS (
    SELECT 
        we.id as endpoint_id,
        we.name as endpoint_name,
        we.url,
        
        -- Delivery statistics
        COUNT(wd.id) as total_deliveries,
        COUNT(wd.id) FILTER (WHERE wd.status = 'SUCCESS') as successful_deliveries,
        COUNT(wd.id) FILTER (WHERE wd.status = 'FAILED') as failed_deliveries,
        COUNT(wd.id) FILTER (WHERE wd.status = 'PENDING') as pending_deliveries,
        
        -- Performance metrics
        AVG(wd.response_time_ms) FILTER (WHERE wd.status = 'SUCCESS') as avg_response_time,
        MAX(wd.delivered_at) as last_successful_delivery,
        
        -- Calculate health score
        CASE 
            WHEN COUNT(wd.id) = 0 THEN 0
            ELSE ROUND(
                COUNT(wd.id) FILTER (WHERE wd.status = 'SUCCESS')::DECIMAL / COUNT(wd.id) * 100, 
                2
            )
        END as success_rate
        
    FROM webhook_endpoints we
    LEFT JOIN webhook_deliveries wd ON wd.webhook_endpoint_id = we.id 
        AND wd.created_at >= NOW() - INTERVAL '24 hours'
    WHERE we.distributor_id = get_current_distributor_id()
    AND we.active = TRUE
    GROUP BY we.id, we.name, we.url
)
SELECT 
    *,
    CASE 
        WHEN success_rate >= 95 THEN 'HEALTHY'
        WHEN success_rate >= 80 THEN 'WARNING' 
        WHEN success_rate >= 50 THEN 'UNHEALTHY'
        ELSE 'CRITICAL'
    END as health_status
FROM webhook_stats
ORDER BY success_rate ASC, total_deliveries DESC;
```

---

### **Example 10: Product Matching Performance**

**Context**: Analyzing how well AI is matching customer requests to products.

```sql
-- Product matching accuracy analysis
WITH matching_stats AS (
    SELECT 
        p.id as product_id,
        p.name as product_name,
        p.category_id,
        pc.name as category_name,
        
        -- Matching attempts
        COUNT(pmh.id) as total_matches_attempted,
        COUNT(pmh.id) FILTER (WHERE pmh.final_product_id = p.id) as correct_matches,
        COUNT(pmh.id) FILTER (WHERE pmh.was_manual_override = TRUE) as manual_corrections,
        
        -- Accuracy metrics
        AVG(pmh.accuracy_rating) FILTER (WHERE pmh.accuracy_rating IS NOT NULL) as avg_accuracy_rating,
        
        -- AI confidence when matched correctly
        AVG(op.matching_confidence) FILTER (WHERE op.matched_product_id = p.id) as avg_matching_confidence,
        
        -- Most common original texts for this product
        array_agg(DISTINCT pmh.original_text ORDER BY pmh.created_at DESC) 
            FILTER (WHERE pmh.final_product_id = p.id) as common_customer_phrases
        
    FROM products p
    LEFT JOIN product_categories pc ON pc.id = p.category_id
    LEFT JOIN product_matching_history pmh ON pmh.final_product_id = p.id
    LEFT JOIN order_products op ON op.matched_product_id = p.id
    WHERE p.distributor_id = get_current_distributor_id()
    AND p.active = TRUE
    GROUP BY p.id, p.name, p.category_id, pc.name
)
SELECT 
    product_name,
    category_name,
    total_matches_attempted,
    correct_matches,
    manual_corrections,
    
    -- Calculate accuracy percentage
    CASE 
        WHEN total_matches_attempted > 0 
        THEN ROUND(correct_matches::DECIMAL / total_matches_attempted * 100, 2)
        ELSE NULL 
    END as accuracy_percentage,
    
    avg_accuracy_rating,
    avg_matching_confidence,
    
    -- Show top 3 customer phrases
    (common_customer_phrases)[1:3] as top_customer_phrases
    
FROM matching_stats
WHERE total_matches_attempted > 0
ORDER BY accuracy_percentage DESC NULLS LAST, total_matches_attempted DESC;
```

---

## 🎯 **Common Query Patterns**

### **Multi-Tenant Filtering Template**
```sql
-- Always include distributor filtering
WHERE table_name.distributor_id = get_current_distributor_id()

-- For joins, ensure all tables are filtered
WHERE c.distributor_id = get_current_distributor_id()
AND o.distributor_id = get_current_distributor_id()
```

### **AI Data Checking Template**
```sql
-- Check if AI processing is complete
WHERE ai_processed = TRUE
AND ai_confidence IS NOT NULL

-- Include confidence-based filtering
WHERE ai_confidence >= 0.7  -- Adjust threshold as needed
```

### **Date Range Filtering Template**
```sql
-- Recent activity (configurable timeframe)
WHERE created_at >= NOW() - INTERVAL '30 days'

-- Business hours only
WHERE EXTRACT(hour FROM created_at) BETWEEN 9 AND 17
AND EXTRACT(dow FROM created_at) BETWEEN 1 AND 5  -- Monday to Friday
```

### **Pagination Template**
```sql
-- Efficient pagination with cursor
WHERE created_at < $cursor_timestamp
ORDER BY created_at DESC
LIMIT $page_size + 1;  -- +1 to check if there are more results
```

These examples provide a solid foundation for working with the AI-powered order management database. Remember to always:

1. **Filter by `distributor_id`** for multi-tenancy
2. **Check AI processing status** before using AI data
3. **Handle NULL values** in AI confidence and extracted data
4. **Use appropriate indexes** for performance
5. **Include error handling** for AI service failures

🚀 Happy coding!