-- Add AI performance monitoring and cost tracking
-- Essential for managing OpenAI API costs and improving AI agent performance
-- Provides detailed analytics for AI usage optimization

-- Enhanced AI usage metrics table
CREATE TABLE ai_usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Time period
    date DATE NOT NULL,
    hour INTEGER CHECK (hour >= 0 AND hour <= 23), -- Hourly granularity for detailed analysis
    
    -- Agent type metrics
    agent_type TEXT NOT NULL CHECK (agent_type IN ('ORDER_PROCESSING', 'CUSTOMER_SUPPORT', 'MESSAGE_ANALYSIS', 'CONTEXT_MANAGER')),
    
    -- Usage counts
    requests_count INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    
    -- Token usage
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    
    -- Cost tracking (in USD cents for precision)
    cost_cents INTEGER DEFAULT 0,
    
    -- Performance metrics
    avg_response_time_ms INTEGER DEFAULT 0,
    min_response_time_ms INTEGER DEFAULT 0,
    max_response_time_ms INTEGER DEFAULT 0,
    
    -- Quality metrics
    avg_confidence DECIMAL(3,2),
    high_confidence_count INTEGER DEFAULT 0, -- confidence >= 0.8
    low_confidence_count INTEGER DEFAULT 0,  -- confidence < 0.5
    
    -- Success metrics
    success_rate DECIMAL(5,4),
    user_acceptance_rate DECIMAL(5,4), -- How often users accept AI suggestions
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, date, hour, agent_type)
);

-- AI model performance comparison table
CREATE TABLE ai_model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Model details
    model_name TEXT NOT NULL, -- 'gpt-4', 'gpt-3.5-turbo', etc.
    model_version TEXT, -- Specific version if available
    agent_type TEXT NOT NULL,
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Performance metrics
    requests_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0,
    avg_confidence DECIMAL(3,2),
    success_rate DECIMAL(5,4),
    cost_per_request_cents INTEGER DEFAULT 0,
    
    -- Quality metrics
    accuracy_score DECIMAL(5,4), -- Based on user feedback
    user_satisfaction DECIMAL(3,2), -- 1-5 scale
    
    -- Token efficiency
    avg_tokens_per_request INTEGER DEFAULT 0,
    cost_per_token_cents DECIMAL(8,6),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, model_name, agent_type, period_start, period_end)
);

-- AI error tracking table
CREATE TABLE ai_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Request details
    agent_type TEXT NOT NULL,
    model_used TEXT,
    request_id TEXT, -- OpenAI request ID if available
    
    -- Error details
    error_type TEXT NOT NULL, -- 'RATE_LIMIT', 'INVALID_REQUEST', 'TIMEOUT', 'PARSE_ERROR', etc.
    error_code TEXT,
    error_message TEXT NOT NULL,
    
    -- Context
    input_text TEXT, -- What was being processed when error occurred
    input_tokens INTEGER,
    
    -- Request metadata
    conversation_id UUID REFERENCES conversations(id),
    message_id UUID REFERENCES messages(id),
    order_id UUID REFERENCES orders(id),
    
    -- Retry information
    retry_count INTEGER DEFAULT 0,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI prompt performance table (for A/B testing prompts)
CREATE TABLE ai_prompt_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Prompt details
    prompt_name TEXT NOT NULL, -- 'order_processing_v1', 'customer_support_v2'
    prompt_version TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    prompt_content TEXT NOT NULL,
    
    -- Test period
    test_start_date DATE NOT NULL,
    test_end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Performance metrics
    usage_count INTEGER DEFAULT 0,
    avg_confidence DECIMAL(3,2),
    success_rate DECIMAL(5,4),
    avg_response_time_ms INTEGER DEFAULT 0,
    
    -- Cost efficiency
    avg_tokens INTEGER DEFAULT 0,
    cost_per_success_cents INTEGER DEFAULT 0,
    
    -- User feedback
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI budget alerts table
CREATE TABLE ai_budget_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Alert details
    alert_type TEXT NOT NULL CHECK (alert_type IN ('BUDGET_WARNING', 'BUDGET_EXCEEDED', 'USAGE_SPIKE', 'ERROR_RATE_HIGH')),
    alert_level TEXT NOT NULL CHECK (alert_level IN ('INFO', 'WARNING', 'CRITICAL')),
    
    -- Budget context
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    budget_limit_cents INTEGER NOT NULL,
    current_spend_cents INTEGER NOT NULL,
    threshold_percentage INTEGER NOT NULL, -- 75%, 90%, 100%, etc.
    
    -- Alert content
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Alert status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_ai_usage_metrics_distributor_date ON ai_usage_metrics(distributor_id, date DESC);
CREATE INDEX idx_ai_usage_metrics_agent_type ON ai_usage_metrics(agent_type, date DESC);
CREATE INDEX idx_ai_usage_metrics_hourly ON ai_usage_metrics(distributor_id, date, hour);

CREATE INDEX idx_ai_model_performance_distributor ON ai_model_performance(distributor_id, period_start DESC);
CREATE INDEX idx_ai_model_performance_model ON ai_model_performance(model_name, agent_type);

CREATE INDEX idx_ai_errors_distributor_date ON ai_errors(distributor_id, created_at DESC);
CREATE INDEX idx_ai_errors_type ON ai_errors(error_type, created_at DESC);
CREATE INDEX idx_ai_errors_unresolved ON ai_errors(resolved, created_at DESC) WHERE resolved = FALSE;

CREATE INDEX idx_ai_prompt_performance_distributor ON ai_prompt_performance(distributor_id, test_start_date DESC);
CREATE INDEX idx_ai_prompt_performance_active ON ai_prompt_performance(agent_type, is_active) WHERE is_active = TRUE;

CREATE INDEX idx_ai_budget_alerts_distributor ON ai_budget_alerts(distributor_id, created_at DESC);
CREATE INDEX idx_ai_budget_alerts_unacknowledged ON ai_budget_alerts(acknowledged, created_at DESC) WHERE acknowledged = FALSE;

-- Function to update AI usage metrics
CREATE OR REPLACE FUNCTION update_ai_usage_metrics(
    dist_id UUID,
    agent_type_param TEXT,
    model_name TEXT,
    input_tokens_count INTEGER,
    output_tokens_count INTEGER,
    response_time_ms INTEGER,
    confidence_score DECIMAL(3,2),
    cost_cents_param INTEGER,
    success BOOLEAN DEFAULT TRUE
)
RETURNS VOID AS $$
DECLARE
    current_date DATE := CURRENT_DATE;
    current_hour INTEGER := EXTRACT(hour FROM NOW());
BEGIN
    -- Insert or update usage metrics
    INSERT INTO ai_usage_metrics (
        distributor_id,
        date,
        hour,
        agent_type,
        requests_count,
        successful_requests,
        failed_requests,
        input_tokens,
        output_tokens,
        total_tokens,
        cost_cents,
        avg_response_time_ms,
        min_response_time_ms,
        max_response_time_ms,
        avg_confidence,
        high_confidence_count,
        low_confidence_count
    ) VALUES (
        dist_id,
        current_date,
        current_hour,
        agent_type_param,
        1,
        CASE WHEN success THEN 1 ELSE 0 END,
        CASE WHEN success THEN 0 ELSE 1 END,
        input_tokens_count,
        output_tokens_count,
        input_tokens_count + output_tokens_count,
        cost_cents_param,
        response_time_ms,
        response_time_ms,
        response_time_ms,
        confidence_score,
        CASE WHEN confidence_score >= 0.8 THEN 1 ELSE 0 END,
        CASE WHEN confidence_score < 0.5 THEN 1 ELSE 0 END
    ) ON CONFLICT (distributor_id, date, hour, agent_type) DO UPDATE SET
        requests_count = ai_usage_metrics.requests_count + 1,
        successful_requests = ai_usage_metrics.successful_requests + CASE WHEN success THEN 1 ELSE 0 END,
        failed_requests = ai_usage_metrics.failed_requests + CASE WHEN success THEN 0 ELSE 1 END,
        input_tokens = ai_usage_metrics.input_tokens + input_tokens_count,
        output_tokens = ai_usage_metrics.output_tokens + output_tokens_count,
        total_tokens = ai_usage_metrics.total_tokens + input_tokens_count + output_tokens_count,
        cost_cents = ai_usage_metrics.cost_cents + cost_cents_param,
        avg_response_time_ms = (ai_usage_metrics.avg_response_time_ms * ai_usage_metrics.requests_count + response_time_ms) / (ai_usage_metrics.requests_count + 1),
        min_response_time_ms = LEAST(ai_usage_metrics.min_response_time_ms, response_time_ms),
        max_response_time_ms = GREATEST(ai_usage_metrics.max_response_time_ms, response_time_ms),
        avg_confidence = (ai_usage_metrics.avg_confidence * ai_usage_metrics.requests_count + confidence_score) / (ai_usage_metrics.requests_count + 1),
        high_confidence_count = ai_usage_metrics.high_confidence_count + CASE WHEN confidence_score >= 0.8 THEN 1 ELSE 0 END,
        low_confidence_count = ai_usage_metrics.low_confidence_count + CASE WHEN confidence_score < 0.5 THEN 1 ELSE 0 END;
        
    -- Update success rate
    UPDATE ai_usage_metrics SET
        success_rate = successful_requests::DECIMAL / GREATEST(requests_count, 1)
    WHERE distributor_id = dist_id 
    AND date = current_date 
    AND hour = current_hour 
    AND agent_type = agent_type_param;
END;
$$ LANGUAGE plpgsql;

-- Function to check budget and create alerts
CREATE OR REPLACE FUNCTION check_ai_budget_and_alert(dist_id UUID)
RETURNS VOID AS $$
DECLARE
    distributor_record distributors%ROWTYPE;
    current_month_start DATE;
    current_month_end DATE;
    current_spend_cents INTEGER;
    budget_cents INTEGER;
    spend_percentage INTEGER;
BEGIN
    -- Get distributor info
    SELECT * INTO distributor_record FROM distributors WHERE id = dist_id;
    
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Calculate current month period
    current_month_start := DATE_TRUNC('month', NOW())::DATE;
    current_month_end := (DATE_TRUNC('month', NOW()) + INTERVAL '1 month - 1 day')::DATE;
    
    -- Get current spend
    SELECT COALESCE(SUM(cost_cents), 0) 
    INTO current_spend_cents
    FROM ai_usage_metrics 
    WHERE distributor_id = dist_id 
    AND date >= current_month_start 
    AND date <= current_month_end;
    
    budget_cents := (distributor_record.monthly_ai_budget_usd * 100)::INTEGER;
    
    IF budget_cents > 0 THEN
        spend_percentage := (current_spend_cents * 100 / budget_cents);
        
        -- Create alerts at different thresholds
        IF spend_percentage >= 100 THEN
            INSERT INTO ai_budget_alerts (
                distributor_id, alert_type, alert_level, period_start, period_end,
                budget_limit_cents, current_spend_cents, threshold_percentage,
                title, message
            ) VALUES (
                dist_id, 'BUDGET_EXCEEDED', 'CRITICAL', current_month_start, current_month_end,
                budget_cents, current_spend_cents, 100,
                'AI Budget Exceeded',
                'Your monthly AI budget has been exceeded. Current spend: $' || (current_spend_cents/100.0)::TEXT || ' / Budget: $' || distributor_record.monthly_ai_budget_usd::TEXT
            ) ON CONFLICT DO NOTHING;
            
        ELSIF spend_percentage >= 90 THEN
            INSERT INTO ai_budget_alerts (
                distributor_id, alert_type, alert_level, period_start, period_end,
                budget_limit_cents, current_spend_cents, threshold_percentage,
                title, message
            ) VALUES (
                dist_id, 'BUDGET_WARNING', 'WARNING', current_month_start, current_month_end,
                budget_cents, current_spend_cents, 90,
                'AI Budget Warning - 90% Used',
                'You have used 90% of your monthly AI budget. Current spend: $' || (current_spend_cents/100.0)::TEXT || ' / Budget: $' || distributor_record.monthly_ai_budget_usd::TEXT
            ) ON CONFLICT DO NOTHING;
            
        ELSIF spend_percentage >= 75 THEN
            INSERT INTO ai_budget_alerts (
                distributor_id, alert_type, alert_level, period_start, period_end,
                budget_limit_cents, current_spend_cents, threshold_percentage,
                title, message
            ) VALUES (
                dist_id, 'BUDGET_WARNING', 'INFO', current_month_start, current_month_end,
                budget_cents, current_spend_cents, 75,
                'AI Budget Notice - 75% Used',
                'You have used 75% of your monthly AI budget. Current spend: $' || (current_spend_cents/100.0)::TEXT || ' / Budget: $' || distributor_record.monthly_ai_budget_usd::TEXT
            ) ON CONFLICT DO NOTHING;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to log AI errors
CREATE OR REPLACE FUNCTION log_ai_error(
    dist_id UUID,
    agent_type_param TEXT,
    error_type_param TEXT,
    error_message_param TEXT,
    input_text_param TEXT DEFAULT NULL,
    conversation_id_param UUID DEFAULT NULL,
    message_id_param UUID DEFAULT NULL,
    order_id_param UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    error_id UUID;
BEGIN
    INSERT INTO ai_errors (
        distributor_id,
        agent_type,
        error_type,
        error_message,
        input_text,
        conversation_id,
        message_id,
        order_id
    ) VALUES (
        dist_id,
        agent_type_param,
        error_type_param,
        error_message_param,
        input_text_param,
        conversation_id_param,
        message_id_param,
        order_id_param
    ) RETURNING id INTO error_id;
    
    RETURN error_id;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for AI dashboard
CREATE MATERIALIZED VIEW ai_dashboard_summary AS
SELECT 
    am.distributor_id,
    am.date,
    am.agent_type,
    SUM(am.requests_count) as total_requests,
    SUM(am.successful_requests) as successful_requests,
    AVG(am.avg_confidence) as avg_confidence,
    SUM(am.total_tokens) as total_tokens,
    SUM(am.cost_cents) as cost_cents,
    AVG(am.avg_response_time_ms) as avg_response_time_ms,
    (SUM(am.successful_requests)::DECIMAL / GREATEST(SUM(am.requests_count), 1)) as success_rate
FROM ai_usage_metrics am
GROUP BY am.distributor_id, am.date, am.agent_type;

-- Create index on materialized view
CREATE INDEX idx_ai_dashboard_summary_distributor_date ON ai_dashboard_summary(distributor_id, date DESC);

-- Function to refresh AI dashboard
CREATE OR REPLACE FUNCTION refresh_ai_dashboard()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ai_dashboard_summary;
END;
$$ LANGUAGE plpgsql;

-- RLS policies for new tables
ALTER TABLE ai_usage_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_model_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_errors ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_prompt_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_budget_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY ai_usage_metrics_tenant_isolation ON ai_usage_metrics
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY ai_model_performance_tenant_isolation ON ai_model_performance
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY ai_errors_tenant_isolation ON ai_errors
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY ai_prompt_performance_tenant_isolation ON ai_prompt_performance
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY ai_budget_alerts_tenant_isolation ON ai_budget_alerts
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON ai_usage_metrics TO distributor_user;
GRANT SELECT ON ai_model_performance TO distributor_user;
GRANT SELECT, INSERT ON ai_errors TO distributor_user;
GRANT SELECT ON ai_prompt_performance TO distributor_user;
GRANT SELECT, UPDATE ON ai_budget_alerts TO distributor_user;
GRANT SELECT ON ai_dashboard_summary TO distributor_user;

GRANT EXECUTE ON FUNCTION update_ai_usage_metrics TO distributor_user;
GRANT EXECUTE ON FUNCTION log_ai_error TO distributor_user;
GRANT EXECUTE ON FUNCTION check_ai_budget_and_alert TO distributor_user;

-- Add comments
COMMENT ON TABLE ai_usage_metrics IS 'Detailed AI usage tracking with hourly granularity for cost and performance monitoring';
COMMENT ON TABLE ai_model_performance IS 'Comparative performance metrics across different AI models';
COMMENT ON TABLE ai_errors IS 'AI error tracking for debugging and reliability monitoring';
COMMENT ON TABLE ai_prompt_performance IS 'A/B testing and performance tracking for different prompts';
COMMENT ON TABLE ai_budget_alerts IS 'Budget monitoring and alerting system for AI costs';

COMMENT ON FUNCTION update_ai_usage_metrics IS 'Updates AI usage metrics after each AI API call';
COMMENT ON FUNCTION check_ai_budget_and_alert IS 'Checks budget usage and creates alerts when thresholds are exceeded';
COMMENT ON FUNCTION log_ai_error IS 'Logs AI errors for monitoring and debugging';