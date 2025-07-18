# Database AI Schema Documentation

## Overview

The AI schema in OrderAgent provides comprehensive data storage and tracking for all AI-powered features. It includes tables for AI responses, performance metrics, cost tracking, training data, and monitoring. The schema is designed to support multi-tenant architecture with proper Row-Level Security (RLS) policies.

## Core AI Tables

### 1. **ai_responses** - AI Response Tracking

**Purpose**: Stores all AI-generated responses and their metadata for analytics and improvement.

**Location**: `supabase/migrations/20240716120006_create_ai_support_tables.sql`

```sql
CREATE TABLE ai_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request context
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- AI processing details
    agent_type TEXT NOT NULL CHECK (agent_type IN (
        'message_processor', 'order_processor', 'customer_service', 
        'analytics', 'escalation_handler'
    )),
    request_type TEXT NOT NULL CHECK (request_type IN (
        'intent_detection', 'entity_extraction', 'sentiment_analysis',
        'order_extraction', 'response_generation', 'customer_analysis',
        'escalation_detection', 'full_analysis'
    )),
    
    -- AI response data
    response_data JSONB NOT NULL,
    confidence_score DECIMAL(4,3) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Performance metrics
    processing_time_ms INTEGER NOT NULL CHECK (processing_time_ms >= 0),
    tokens_used INTEGER NOT NULL CHECK (tokens_used >= 0),
    cost_usd DECIMAL(8,6) NOT NULL CHECK (cost_usd >= 0),
    
    -- Model information
    model_used TEXT NOT NULL DEFAULT 'gpt-4',
    model_version TEXT,
    
    -- Quality indicators
    human_review_required BOOLEAN DEFAULT FALSE,
    human_feedback_score INTEGER CHECK (human_feedback_score >= 1 AND human_feedback_score <= 5),
    human_feedback_notes TEXT,
    
    -- Status tracking
    status TEXT DEFAULT 'COMPLETED' CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    error_message TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_ai_responses_message_id ON ai_responses(message_id);
CREATE INDEX idx_ai_responses_conversation_id ON ai_responses(conversation_id);
CREATE INDEX idx_ai_responses_distributor_id ON ai_responses(distributor_id);
CREATE INDEX idx_ai_responses_agent_type ON ai_responses(agent_type);
CREATE INDEX idx_ai_responses_created_at ON ai_responses(created_at DESC);
CREATE INDEX idx_ai_responses_cost_tracking ON ai_responses(distributor_id, created_at DESC, cost_usd);

-- Composite indexes for analytics
CREATE INDEX idx_ai_responses_analytics ON ai_responses(
    distributor_id, agent_type, request_type, created_at DESC
);
```

**Sample Data Structure**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "message_id": "msg_123",
  "agent_type": "message_processor",
  "request_type": "full_analysis",
  "response_data": {
    "intent": "ORDER_REQUEST",
    "entities": {
      "products": ["apples", "oranges"],
      "quantities": [5, 10],
      "delivery_date": "2024-07-20"
    },
    "sentiment": {
      "sentiment": "POSITIVE",
      "confidence": 0.85,
      "urgency_level": "MEDIUM"
    }
  },
  "confidence_score": 0.85,
  "processing_time_ms": 1250,
  "tokens_used": 450,
  "cost_usd": 0.0135,
  "model_used": "gpt-4"
}
```

### 2. **ai_training_data** - Training and Improvement Data

**Purpose**: Stores training data, corrections, and feedback for model improvement.

```sql
CREATE TABLE ai_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Data context
    distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Training data
    original_input TEXT NOT NULL,
    ai_output JSONB NOT NULL,
    human_correction JSONB,
    
    -- Categorization
    data_type TEXT NOT NULL CHECK (data_type IN (
        'INTENT_CLASSIFICATION', 'ENTITY_EXTRACTION', 'SENTIMENT_ANALYSIS',
        'ORDER_PROCESSING', 'RESPONSE_GENERATION', 'CUSTOMER_ANALYSIS'
    )),
    correction_type TEXT CHECK (correction_type IN (
        'INTENT_CORRECTION', 'ENTITY_CORRECTION', 'SENTIMENT_CORRECTION',
        'RESPONSE_IMPROVEMENT', 'ESCALATION_CORRECTION'
    )),
    
    -- Quality metrics
    improvement_score DECIMAL(4,3) CHECK (improvement_score >= -1 AND improvement_score <= 1),
    confidence_before DECIMAL(4,3),
    confidence_after DECIMAL(4,3),
    
    -- Source tracking
    data_source TEXT NOT NULL CHECK (data_source IN (
        'HUMAN_CORRECTION', 'AUTOMATED_FEEDBACK', 'MANUAL_ENTRY',
        'QUALITY_REVIEW', 'CUSTOMER_FEEDBACK', 'A_B_TEST'
    )),
    reviewer_id UUID,
    
    -- Status
    is_validated BOOLEAN DEFAULT FALSE,
    is_used_for_training BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ai_training_data_distributor ON ai_training_data(distributor_id);
CREATE INDEX idx_ai_training_data_type ON ai_training_data(data_type);
CREATE INDEX idx_ai_training_data_validation ON ai_training_data(is_validated, is_used_for_training);
```

### 3. **ai_usage_metrics** - Usage and Cost Tracking

**Purpose**: Tracks AI usage, costs, and performance metrics for billing and optimization.

**Location**: `supabase/migrations/20240717120012_add_ai_monitoring.sql`

```sql
CREATE TABLE ai_usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Tenant context
    distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Time period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    aggregation_level TEXT NOT NULL CHECK (aggregation_level IN ('HOUR', 'DAY', 'WEEK', 'MONTH')),
    
    -- Usage metrics by agent type
    message_processor_requests INTEGER DEFAULT 0,
    message_processor_tokens INTEGER DEFAULT 0,
    message_processor_cost_usd DECIMAL(10,6) DEFAULT 0,
    
    order_processor_requests INTEGER DEFAULT 0,
    order_processor_tokens INTEGER DEFAULT 0,
    order_processor_cost_usd DECIMAL(10,6) DEFAULT 0,
    
    customer_service_requests INTEGER DEFAULT 0,
    customer_service_tokens INTEGER DEFAULT 0,
    customer_service_cost_usd DECIMAL(10,6) DEFAULT 0,
    
    analytics_requests INTEGER DEFAULT 0,
    analytics_tokens INTEGER DEFAULT 0,
    analytics_cost_usd DECIMAL(10,6) DEFAULT 0,
    
    -- Totals
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0,
    
    -- Performance metrics
    avg_processing_time_ms INTEGER,
    avg_confidence_score DECIMAL(4,3),
    success_rate DECIMAL(4,3),
    
    -- Error tracking
    error_count INTEGER DEFAULT 0,
    timeout_count INTEGER DEFAULT 0,
    
    -- Quality metrics
    human_review_rate DECIMAL(4,3),
    customer_satisfaction_score DECIMAL(4,3),
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique periods per distributor
    UNIQUE(distributor_id, period_start, period_end, aggregation_level)
);

-- Indexes for performance
CREATE INDEX idx_ai_usage_metrics_distributor_period ON ai_usage_metrics(
    distributor_id, period_start DESC
);
CREATE INDEX idx_ai_usage_metrics_aggregation ON ai_usage_metrics(
    aggregation_level, period_start DESC
);
```

### 4. **ai_model_performance** - Model Performance Tracking

**Purpose**: Tracks performance metrics for different AI models and configurations.

```sql
CREATE TABLE ai_model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model identification
    model_name TEXT NOT NULL,
    model_version TEXT,
    agent_type TEXT NOT NULL,
    
    -- Performance period
    evaluation_period_start TIMESTAMPTZ NOT NULL,
    evaluation_period_end TIMESTAMPTZ NOT NULL,
    
    -- Performance metrics
    total_requests INTEGER NOT NULL DEFAULT 0,
    successful_requests INTEGER NOT NULL DEFAULT 0,
    failed_requests INTEGER NOT NULL DEFAULT 0,
    
    -- Accuracy metrics
    accuracy_score DECIMAL(4,3),
    precision_score DECIMAL(4,3),
    recall_score DECIMAL(4,3),
    f1_score DECIMAL(4,3),
    
    -- Confidence metrics
    avg_confidence DECIMAL(4,3),
    confidence_calibration DECIMAL(4,3),
    
    -- Performance metrics
    avg_processing_time_ms INTEGER,
    p95_processing_time_ms INTEGER,
    p99_processing_time_ms INTEGER,
    
    -- Cost metrics
    avg_cost_per_request DECIMAL(8,6),
    avg_tokens_per_request INTEGER,
    
    -- Quality metrics
    human_feedback_score DECIMAL(4,3),
    customer_satisfaction_score DECIMAL(4,3),
    
    -- Benchmark data
    benchmark_dataset TEXT,
    benchmark_score DECIMAL(4,3),
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ai_model_performance_model ON ai_model_performance(
    model_name, model_version, agent_type
);
CREATE INDEX idx_ai_model_performance_period ON ai_model_performance(
    evaluation_period_start DESC
);
```

### 5. **ai_budget_alerts** - Budget Management

**Purpose**: Manages AI usage budgets and alerts for cost control.

```sql
CREATE TABLE ai_budget_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Budget context
    distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Budget settings
    budget_period TEXT NOT NULL CHECK (budget_period IN ('DAILY', 'WEEKLY', 'MONTHLY')),
    budget_amount_usd DECIMAL(10,2) NOT NULL,
    current_spend_usd DECIMAL(10,2) DEFAULT 0,
    
    -- Alert thresholds
    alert_threshold_50 BOOLEAN DEFAULT TRUE,
    alert_threshold_75 BOOLEAN DEFAULT TRUE,
    alert_threshold_90 BOOLEAN DEFAULT TRUE,
    alert_threshold_100 BOOLEAN DEFAULT TRUE,
    
    -- Alert status
    alerts_sent JSONB DEFAULT '[]',
    budget_exceeded BOOLEAN DEFAULT FALSE,
    ai_disabled BOOLEAN DEFAULT FALSE,
    
    -- Period tracking
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one budget per distributor per period
    UNIQUE(distributor_id, period_start, period_end)
);

-- Indexes
CREATE INDEX idx_ai_budget_alerts_distributor ON ai_budget_alerts(distributor_id);
CREATE INDEX idx_ai_budget_alerts_period ON ai_budget_alerts(period_start DESC);
CREATE INDEX idx_ai_budget_alerts_exceeded ON ai_budget_alerts(budget_exceeded, ai_disabled);
```

### 6. **ai_prompt_templates** - Prompt Management

**Purpose**: Manages AI prompts for different use cases and A/B testing.

```sql
CREATE TABLE ai_prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template identification
    template_name TEXT NOT NULL,
    template_version TEXT NOT NULL DEFAULT 'v1',
    agent_type TEXT NOT NULL,
    request_type TEXT NOT NULL,
    
    -- Template content
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    
    -- Template configuration
    model_config JSONB DEFAULT '{}',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    
    -- Status and testing
    is_active BOOLEAN DEFAULT TRUE,
    is_a_b_test BOOLEAN DEFAULT FALSE,
    a_b_test_percentage DECIMAL(4,3) DEFAULT 0.5,
    
    -- Performance tracking
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(4,3),
    avg_confidence DECIMAL(4,3),
    avg_processing_time_ms INTEGER,
    
    -- Audit
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique active templates per type
    UNIQUE(template_name, agent_type, request_type, is_active) WHERE is_active = TRUE
);

-- Indexes
CREATE INDEX idx_ai_prompt_templates_type ON ai_prompt_templates(agent_type, request_type);
CREATE INDEX idx_ai_prompt_templates_active ON ai_prompt_templates(is_active, is_a_b_test);
```

## Enhanced Message Schema

### Updated messages table with AI fields

```sql
-- Add AI-specific columns to existing messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_processed BOOLEAN DEFAULT FALSE;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_confidence DECIMAL(4,3);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_extracted_intent TEXT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_extracted_products JSONB;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_suggested_responses JSONB;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_sentiment_score DECIMAL(4,3);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_urgency_level TEXT CHECK (
    ai_urgency_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_requires_human_review BOOLEAN DEFAULT FALSE;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ai_processing_errors JSONB;

-- Index for AI-processed messages
CREATE INDEX idx_messages_ai_processed ON messages(ai_processed, ai_confidence DESC);
CREATE INDEX idx_messages_ai_review ON messages(ai_requires_human_review, created_at DESC);
```

### Updated conversations table with AI insights

```sql
-- Add AI context to conversations
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ai_context_summary TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ai_customer_sentiment TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ai_escalation_risk DECIMAL(4,3);
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ai_order_intent_detected BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS ai_last_analysis_at TIMESTAMPTZ;

-- Index for AI insights
CREATE INDEX idx_conversations_ai_insights ON conversations(
    ai_escalation_risk DESC, ai_customer_sentiment
);
```

## Database Functions

### 1. **AI Response Analytics Function**

```sql
CREATE OR REPLACE FUNCTION get_ai_performance_metrics(
    distributor_uuid UUID,
    start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
    end_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE(
    agent_type TEXT,
    total_requests BIGINT,
    avg_confidence DECIMAL,
    avg_processing_time INTEGER,
    total_cost DECIMAL,
    success_rate DECIMAL,
    human_review_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ar.agent_type,
        COUNT(ar.id) as total_requests,
        AVG(ar.confidence_score) as avg_confidence,
        AVG(ar.processing_time_ms)::INTEGER as avg_processing_time,
        SUM(ar.cost_usd) as total_cost,
        (COUNT(ar.id) FILTER (WHERE ar.status = 'COMPLETED')::DECIMAL / COUNT(ar.id)) as success_rate,
        (COUNT(ar.id) FILTER (WHERE ar.human_review_required = TRUE)::DECIMAL / COUNT(ar.id)) as human_review_rate
    FROM ai_responses ar
    WHERE ar.distributor_id = distributor_uuid
      AND ar.created_at >= start_date
      AND ar.created_at <= end_date
    GROUP BY ar.agent_type
    ORDER BY total_requests DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 2. **Budget Monitoring Function**

```sql
CREATE OR REPLACE FUNCTION update_ai_budget_spend(
    distributor_uuid UUID,
    additional_cost DECIMAL
)
RETURNS VOID AS $$
DECLARE
    current_budget RECORD;
    alert_needed BOOLEAN := FALSE;
    alert_threshold INTEGER;
BEGIN
    -- Get current budget period
    SELECT * INTO current_budget
    FROM ai_budget_alerts
    WHERE distributor_id = distributor_uuid
      AND period_start <= NOW()
      AND period_end >= NOW()
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF current_budget.id IS NOT NULL THEN
        -- Update current spend
        UPDATE ai_budget_alerts
        SET current_spend_usd = current_spend_usd + additional_cost,
            updated_at = NOW()
        WHERE id = current_budget.id;
        
        -- Check if alerts need to be sent
        DECLARE
            spend_percentage DECIMAL := (current_budget.current_spend_usd + additional_cost) / current_budget.budget_amount_usd;
        BEGIN
            IF spend_percentage >= 1.0 AND NOT (current_budget.alerts_sent->>'100')::BOOLEAN THEN
                -- Send 100% alert and disable AI
                UPDATE ai_budget_alerts
                SET alerts_sent = alerts_sent || jsonb_build_object('100', TRUE),
                    budget_exceeded = TRUE,
                    ai_disabled = TRUE
                WHERE id = current_budget.id;
                
                -- TODO: Send alert notification
                
            ELSIF spend_percentage >= 0.9 AND NOT (current_budget.alerts_sent->>'90')::BOOLEAN THEN
                UPDATE ai_budget_alerts
                SET alerts_sent = alerts_sent || jsonb_build_object('90', TRUE)
                WHERE id = current_budget.id;
                
            ELSIF spend_percentage >= 0.75 AND NOT (current_budget.alerts_sent->>'75')::BOOLEAN THEN
                UPDATE ai_budget_alerts
                SET alerts_sent = alerts_sent || jsonb_build_object('75', TRUE)
                WHERE id = current_budget.id;
                
            ELSIF spend_percentage >= 0.5 AND NOT (current_budget.alerts_sent->>'50')::BOOLEAN THEN
                UPDATE ai_budget_alerts
                SET alerts_sent = alerts_sent || jsonb_build_object('50', TRUE)
                WHERE id = current_budget.id;
            END IF;
        END;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 3. **AI Quality Scoring Function**

```sql
CREATE OR REPLACE FUNCTION calculate_ai_quality_score(
    conversation_uuid UUID
)
RETURNS DECIMAL AS $$
DECLARE
    avg_confidence DECIMAL;
    human_review_rate DECIMAL;
    customer_satisfaction DECIMAL;
    response_time_score DECIMAL;
    quality_score DECIMAL;
BEGIN
    -- Calculate average confidence for the conversation
    SELECT AVG(confidence_score) INTO avg_confidence
    FROM ai_responses
    WHERE conversation_id = conversation_uuid;
    
    -- Calculate human review rate
    SELECT 
        COUNT(*) FILTER (WHERE human_review_required = TRUE)::DECIMAL / COUNT(*)
    INTO human_review_rate
    FROM ai_responses
    WHERE conversation_id = conversation_uuid;
    
    -- Get customer satisfaction (mock calculation)
    SELECT 0.8 INTO customer_satisfaction; -- Would come from actual feedback
    
    -- Calculate response time score (faster = better)
    SELECT 
        CASE 
            WHEN AVG(processing_time_ms) < 1000 THEN 1.0
            WHEN AVG(processing_time_ms) < 3000 THEN 0.8
            WHEN AVG(processing_time_ms) < 5000 THEN 0.6
            ELSE 0.4
        END
    INTO response_time_score
    FROM ai_responses
    WHERE conversation_id = conversation_uuid;
    
    -- Calculate weighted quality score
    quality_score := (
        COALESCE(avg_confidence, 0) * 0.3 +
        (1 - COALESCE(human_review_rate, 0)) * 0.2 +
        COALESCE(customer_satisfaction, 0) * 0.3 +
        COALESCE(response_time_score, 0) * 0.2
    );
    
    RETURN quality_score;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Row-Level Security (RLS) Policies

### AI Tables Security

```sql
-- Enable RLS on AI tables
ALTER TABLE ai_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_training_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_usage_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_model_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_budget_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_prompt_templates ENABLE ROW LEVEL SECURITY;

-- AI responses policies
CREATE POLICY ai_responses_tenant_isolation ON ai_responses
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

-- AI training data policies
CREATE POLICY ai_training_data_tenant_isolation ON ai_training_data
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

-- AI usage metrics policies
CREATE POLICY ai_usage_metrics_tenant_isolation ON ai_usage_metrics
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

-- AI budget alerts policies
CREATE POLICY ai_budget_alerts_tenant_isolation ON ai_budget_alerts
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

-- AI prompt templates policies (some templates may be global)
CREATE POLICY ai_prompt_templates_access ON ai_prompt_templates
    FOR SELECT USING (
        created_by = get_current_distributor_id() OR 
        created_by IS NULL OR -- Global templates
        is_service_role()
    );
```

## Materialized Views for Performance

### AI Performance Dashboard View

```sql
CREATE MATERIALIZED VIEW ai_performance_dashboard AS
SELECT 
    um.distributor_id,
    um.period_start,
    um.period_end,
    um.total_requests,
    um.total_cost_usd,
    um.avg_confidence_score,
    um.success_rate,
    um.human_review_rate,
    d.business_name,
    d.subscription_tier,
    -- Cost efficiency metrics
    CASE 
        WHEN um.total_requests > 0 THEN um.total_cost_usd / um.total_requests
        ELSE 0
    END as cost_per_request,
    -- Performance ratings
    CASE 
        WHEN um.avg_confidence_score > 0.8 THEN 'EXCELLENT'
        WHEN um.avg_confidence_score > 0.7 THEN 'GOOD'
        WHEN um.avg_confidence_score > 0.6 THEN 'FAIR'
        ELSE 'POOR'
    END as performance_rating
FROM ai_usage_metrics um
JOIN distributors d ON d.id = um.distributor_id
WHERE um.aggregation_level = 'DAY'
ORDER BY um.period_start DESC;

-- Refresh schedule for materialized view
CREATE OR REPLACE FUNCTION refresh_ai_performance_dashboard()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW ai_performance_dashboard;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh every hour
SELECT cron.schedule('refresh-ai-dashboard', '0 * * * *', 'SELECT refresh_ai_performance_dashboard();');
```

## Backup and Archival

### Data Retention Policies

```sql
-- Archive old AI responses (keep 1 year)
CREATE OR REPLACE FUNCTION archive_old_ai_responses()
RETURNS VOID AS $$
BEGIN
    -- Move old responses to archive table
    INSERT INTO ai_responses_archive 
    SELECT * FROM ai_responses 
    WHERE created_at < NOW() - INTERVAL '1 year';
    
    -- Delete archived responses
    DELETE FROM ai_responses 
    WHERE created_at < NOW() - INTERVAL '1 year';
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly archival
SELECT cron.schedule('archive-ai-responses', '0 0 1 * *', 'SELECT archive_old_ai_responses();');
```

## Query Examples

### Common AI Analytics Queries

```sql
-- Daily AI usage by agent type
SELECT 
    DATE(created_at) as date,
    agent_type,
    COUNT(*) as requests,
    AVG(confidence_score) as avg_confidence,
    SUM(cost_usd) as total_cost
FROM ai_responses
WHERE distributor_id = 'your-distributor-id'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), agent_type
ORDER BY date DESC, agent_type;

-- Top expensive AI operations
SELECT 
    agent_type,
    request_type,
    COUNT(*) as request_count,
    SUM(cost_usd) as total_cost,
    AVG(cost_usd) as avg_cost,
    AVG(tokens_used) as avg_tokens
FROM ai_responses
WHERE distributor_id = 'your-distributor-id'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY agent_type, request_type
ORDER BY total_cost DESC;

-- AI quality metrics
SELECT 
    agent_type,
    AVG(confidence_score) as avg_confidence,
    COUNT(*) FILTER (WHERE human_review_required = TRUE)::DECIMAL / COUNT(*) as review_rate,
    AVG(processing_time_ms) as avg_processing_time
FROM ai_responses
WHERE distributor_id = 'your-distributor-id'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY agent_type
ORDER BY avg_confidence DESC;
```

---

*The AI database schema provides comprehensive tracking and analytics for all AI operations while maintaining security, performance, and scalability requirements.*