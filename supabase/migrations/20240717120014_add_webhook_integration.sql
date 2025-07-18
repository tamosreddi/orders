-- Add webhook integration support for external systems
-- Enables real-time notifications and integrations with WhatsApp, SMS, Email providers
-- Essential for the AI-powered messaging platform to connect with external services

-- Webhook endpoints configuration
CREATE TABLE webhook_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Endpoint details
    name TEXT NOT NULL, -- 'WhatsApp Business API', 'Twilio SMS', 'SendGrid Email'
    url TEXT NOT NULL,
    method TEXT CHECK (method IN ('POST', 'PUT', 'PATCH')) DEFAULT 'POST',
    
    -- Authentication
    auth_type TEXT CHECK (auth_type IN ('NONE', 'BEARER_TOKEN', 'API_KEY', 'BASIC_AUTH', 'SIGNATURE')) DEFAULT 'NONE',
    auth_header_name TEXT, -- 'Authorization', 'X-API-Key', etc.
    auth_secret_id TEXT, -- Reference to encrypted secret storage
    
    -- Webhook configuration
    events TEXT[] NOT NULL DEFAULT '{}', -- Array of events this webhook subscribes to
    active BOOLEAN DEFAULT TRUE,
    
    -- Request configuration
    content_type TEXT DEFAULT 'application/json',
    custom_headers JSONB DEFAULT '{}'::jsonb,
    timeout_seconds INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 5,
    
    -- Filtering
    filter_conditions JSONB DEFAULT '{}'::jsonb, -- Conditions for when to trigger webhook
    
    -- Status and monitoring
    last_triggered_at TIMESTAMPTZ,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_error TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Webhook delivery attempts and logs
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_endpoint_id UUID NOT NULL REFERENCES webhook_endpoints(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Trigger details
    event_type TEXT NOT NULL, -- 'message.received', 'order.created', 'customer.updated'
    event_data JSONB NOT NULL, -- The actual event payload
    
    -- Related records
    conversation_id UUID REFERENCES conversations(id),
    message_id UUID REFERENCES messages(id),
    order_id UUID REFERENCES orders(id),
    customer_id UUID REFERENCES customers(id),
    
    -- Delivery attempt details
    attempt_number INTEGER DEFAULT 1,
    max_attempts INTEGER DEFAULT 3,
    
    -- Request details
    request_url TEXT NOT NULL,
    request_method TEXT NOT NULL,
    request_headers JSONB,
    request_body TEXT,
    
    -- Response details
    response_status_code INTEGER,
    response_headers JSONB,
    response_body TEXT,
    response_time_ms INTEGER,
    
    -- Delivery status
    status TEXT CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'RETRYING', 'ABANDONED')) DEFAULT 'PENDING',
    error_message TEXT,
    
    -- Timing
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- External system integrations
CREATE TABLE external_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Integration details
    integration_name TEXT NOT NULL, -- 'WhatsApp Business', 'Twilio', 'SendGrid', 'Shopify'
    integration_type TEXT CHECK (integration_type IN ('MESSAGING', 'ECOMMERCE', 'CRM', 'ANALYTICS', 'PAYMENT')) NOT NULL,
    provider TEXT NOT NULL, -- 'Meta', 'Twilio', 'SendGrid', etc.
    
    -- Configuration
    config JSONB NOT NULL DEFAULT '{}'::jsonb, -- Provider-specific configuration
    credentials_secret_id TEXT, -- Reference to encrypted credentials
    
    -- Capabilities
    supports_inbound BOOLEAN DEFAULT FALSE, -- Can receive messages/data
    supports_outbound BOOLEAN DEFAULT FALSE, -- Can send messages/data
    supports_webhooks BOOLEAN DEFAULT FALSE,
    
    -- Status
    status TEXT CHECK (status IN ('ACTIVE', 'INACTIVE', 'ERROR', 'SETUP_REQUIRED')) DEFAULT 'SETUP_REQUIRED',
    last_sync_at TIMESTAMPTZ,
    sync_frequency INTERVAL DEFAULT '15 minutes',
    
    -- Error handling
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    last_successful_sync_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, integration_name)
);

-- External message mapping (for inbound messages)
CREATE TABLE external_message_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES external_integrations(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- External system identifiers
    external_message_id TEXT NOT NULL,
    external_conversation_id TEXT,
    external_customer_id TEXT,
    
    -- Internal mappings
    message_id UUID REFERENCES messages(id),
    conversation_id UUID REFERENCES conversations(id),
    customer_id UUID REFERENCES customers(id),
    
    -- Message metadata
    external_timestamp TIMESTAMPTZ,
    external_status TEXT,
    external_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Sync status
    sync_status TEXT CHECK (sync_status IN ('PENDING', 'SYNCED', 'FAILED', 'CONFLICT')) DEFAULT 'PENDING',
    sync_attempts INTEGER DEFAULT 0,
    last_sync_attempt TIMESTAMPTZ,
    sync_error TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(integration_id, external_message_id)
);

-- API rate limiting
CREATE TABLE api_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Rate limit scope
    api_endpoint TEXT NOT NULL, -- '/api/messages', '/api/ai/chat', etc.
    integration_id UUID REFERENCES external_integrations(id), -- Specific to integration
    
    -- Rate limit configuration
    requests_per_minute INTEGER DEFAULT 60,
    requests_per_hour INTEGER DEFAULT 1000,
    requests_per_day INTEGER DEFAULT 10000,
    
    -- Current usage (resets periodically)
    current_minute_count INTEGER DEFAULT 0,
    current_hour_count INTEGER DEFAULT 0,
    current_day_count INTEGER DEFAULT 0,
    
    -- Reset timestamps
    minute_reset_at TIMESTAMPTZ DEFAULT NOW(),
    hour_reset_at TIMESTAMPTZ DEFAULT NOW(),
    day_reset_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Webhook event templates
CREATE TABLE webhook_event_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE, -- NULL for global templates
    
    -- Template details
    event_type TEXT NOT NULL,
    template_name TEXT NOT NULL,
    description TEXT,
    
    -- Template structure
    payload_template JSONB NOT NULL, -- JSON template with variables
    required_fields TEXT[] DEFAULT '{}',
    optional_fields TEXT[] DEFAULT '{}',
    
    -- Transformation rules
    field_mappings JSONB DEFAULT '{}'::jsonb, -- How to map internal fields to external format
    custom_transformations TEXT, -- Custom transformation logic
    
    -- Validation
    schema_validation JSONB, -- JSON schema for validation
    
    -- Usage
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, event_type, template_name)
);

-- Create indexes for performance
CREATE INDEX idx_webhook_endpoints_distributor ON webhook_endpoints(distributor_id, active) WHERE active = TRUE;
CREATE INDEX idx_webhook_endpoints_events ON webhook_endpoints USING GIN (events);

CREATE INDEX idx_webhook_deliveries_endpoint ON webhook_deliveries(webhook_endpoint_id, created_at DESC);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status, scheduled_at) WHERE status IN ('PENDING', 'RETRYING');
CREATE INDEX idx_webhook_deliveries_distributor ON webhook_deliveries(distributor_id, created_at DESC);

CREATE INDEX idx_external_integrations_distributor ON external_integrations(distributor_id, status);
CREATE INDEX idx_external_integrations_type ON external_integrations(integration_type, status);

CREATE INDEX idx_external_message_mappings_integration ON external_message_mappings(integration_id, sync_status);
CREATE INDEX idx_external_message_mappings_external_id ON external_message_mappings(external_message_id);

CREATE INDEX idx_api_rate_limits_distributor ON api_rate_limits(distributor_id, api_endpoint);
CREATE INDEX idx_api_rate_limits_endpoint ON api_rate_limits(api_endpoint, active) WHERE active = TRUE;

CREATE INDEX idx_webhook_event_templates_distributor ON webhook_event_templates(distributor_id, event_type) WHERE active = TRUE;

-- Function to trigger webhook delivery
CREATE OR REPLACE FUNCTION trigger_webhook_delivery(
    event_type_param TEXT,
    event_data_param JSONB,
    dist_id UUID,
    conversation_id_param UUID DEFAULT NULL,
    message_id_param UUID DEFAULT NULL,
    order_id_param UUID DEFAULT NULL,
    customer_id_param UUID DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    webhook_record webhook_endpoints%ROWTYPE;
    delivery_count INTEGER := 0;
BEGIN
    -- Find all active webhooks that subscribe to this event type
    FOR webhook_record IN 
        SELECT * FROM webhook_endpoints 
        WHERE distributor_id = dist_id 
        AND active = TRUE 
        AND event_type_param = ANY(events)
    LOOP
        -- Create webhook delivery record
        INSERT INTO webhook_deliveries (
            webhook_endpoint_id,
            distributor_id,
            event_type,
            event_data,
            conversation_id,
            message_id,
            order_id,
            customer_id,
            request_url,
            request_method,
            max_attempts
        ) VALUES (
            webhook_record.id,
            dist_id,
            event_type_param,
            event_data_param,
            conversation_id_param,
            message_id_param,
            order_id_param,
            customer_id_param,
            webhook_record.url,
            webhook_record.method,
            webhook_record.retry_attempts
        );
        
        delivery_count := delivery_count + 1;
    END LOOP;
    
    RETURN delivery_count;
END;
$$ LANGUAGE plpgsql;

-- Function to check and update rate limits
CREATE OR REPLACE FUNCTION check_rate_limit(
    dist_id UUID,
    endpoint_param TEXT,
    integration_id_param UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    rate_limit_record api_rate_limits%ROWTYPE;
    current_time TIMESTAMPTZ := NOW();
BEGIN
    -- Get or create rate limit record
    SELECT * INTO rate_limit_record
    FROM api_rate_limits 
    WHERE distributor_id = dist_id 
    AND api_endpoint = endpoint_param
    AND (integration_id = integration_id_param OR (integration_id IS NULL AND integration_id_param IS NULL))
    AND active = TRUE;
    
    IF NOT FOUND THEN
        -- Create default rate limit
        INSERT INTO api_rate_limits (distributor_id, api_endpoint, integration_id)
        VALUES (dist_id, endpoint_param, integration_id_param);
        RETURN TRUE; -- Allow first request
    END IF;
    
    -- Reset counters if time periods have passed
    IF current_time >= rate_limit_record.minute_reset_at + INTERVAL '1 minute' THEN
        UPDATE api_rate_limits 
        SET current_minute_count = 0, minute_reset_at = current_time
        WHERE id = rate_limit_record.id;
        rate_limit_record.current_minute_count := 0;
    END IF;
    
    IF current_time >= rate_limit_record.hour_reset_at + INTERVAL '1 hour' THEN
        UPDATE api_rate_limits 
        SET current_hour_count = 0, hour_reset_at = current_time
        WHERE id = rate_limit_record.id;
        rate_limit_record.current_hour_count := 0;
    END IF;
    
    IF current_time >= rate_limit_record.day_reset_at + INTERVAL '1 day' THEN
        UPDATE api_rate_limits 
        SET current_day_count = 0, day_reset_at = current_time
        WHERE id = rate_limit_record.id;
        rate_limit_record.current_day_count := 0;
    END IF;
    
    -- Check if limits are exceeded
    IF rate_limit_record.current_minute_count >= rate_limit_record.requests_per_minute OR
       rate_limit_record.current_hour_count >= rate_limit_record.requests_per_hour OR
       rate_limit_record.current_day_count >= rate_limit_record.requests_per_day THEN
        RETURN FALSE; -- Rate limit exceeded
    END IF;
    
    -- Increment counters
    UPDATE api_rate_limits 
    SET 
        current_minute_count = current_minute_count + 1,
        current_hour_count = current_hour_count + 1,
        current_day_count = current_day_count + 1,
        updated_at = current_time
    WHERE id = rate_limit_record.id;
    
    RETURN TRUE; -- Request allowed
END;
$$ LANGUAGE plpgsql;

-- Function to process webhook delivery queue
CREATE OR REPLACE FUNCTION process_webhook_delivery_queue()
RETURNS INTEGER AS $$
DECLARE
    delivery_record webhook_deliveries%ROWTYPE;
    processed_count INTEGER := 0;
BEGIN
    -- Process pending and retrying webhooks
    FOR delivery_record IN 
        SELECT * FROM webhook_deliveries 
        WHERE status IN ('PENDING', 'RETRYING')
        AND scheduled_at <= NOW()
        AND attempt_number <= max_attempts
        ORDER BY scheduled_at ASC
        LIMIT 100 -- Process in batches
    LOOP
        -- Update attempt number
        UPDATE webhook_deliveries 
        SET 
            attempt_number = attempt_number + 1,
            status = 'RETRYING'
        WHERE id = delivery_record.id;
        
        -- Here you would make the actual HTTP request
        -- For now, we'll simulate success/failure
        -- In real implementation, this would use an HTTP client
        
        processed_count := processed_count + 1;
    END LOOP;
    
    -- Mark abandoned deliveries
    UPDATE webhook_deliveries 
    SET status = 'ABANDONED'
    WHERE status IN ('PENDING', 'RETRYING')
    AND attempt_number > max_attempts;
    
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically create webhook deliveries for important events
CREATE OR REPLACE FUNCTION auto_trigger_webhooks()
RETURNS TRIGGER AS $$
DECLARE
    event_type_var TEXT;
    event_data_var JSONB;
    dist_id UUID;
BEGIN
    -- Determine event type and data based on the table
    CASE TG_TABLE_NAME
        WHEN 'messages' THEN
            event_type_var := 'message.' || CASE WHEN TG_OP = 'INSERT' THEN 'created' ELSE 'updated' END;
            SELECT c.distributor_id INTO dist_id FROM conversations c WHERE c.id = NEW.conversation_id;
            event_data_var := jsonb_build_object(
                'message_id', NEW.id,
                'conversation_id', NEW.conversation_id,
                'content', NEW.content,
                'is_from_customer', NEW.is_from_customer,
                'created_at', NEW.created_at
            );
            
        WHEN 'orders' THEN
            event_type_var := 'order.' || CASE WHEN TG_OP = 'INSERT' THEN 'created' ELSE 'updated' END;
            dist_id := NEW.distributor_id;
            event_data_var := jsonb_build_object(
                'order_id', NEW.id,
                'customer_id', NEW.customer_id,
                'status', NEW.status,
                'total_amount', NEW.total_amount,
                'created_at', NEW.created_at
            );
            
        WHEN 'customers' THEN
            event_type_var := 'customer.' || CASE WHEN TG_OP = 'INSERT' THEN 'created' ELSE 'updated' END;
            dist_id := NEW.distributor_id;
            event_data_var := jsonb_build_object(
                'customer_id', NEW.id,
                'business_name', NEW.business_name,
                'status', NEW.status,
                'created_at', NEW.created_at
            );
            
        ELSE
            RETURN NEW; -- Skip for other tables
    END CASE;
    
    -- Trigger webhook deliveries
    PERFORM trigger_webhook_delivery(
        event_type_var,
        event_data_var,
        dist_id,
        CASE WHEN TG_TABLE_NAME = 'messages' THEN NEW.conversation_id END,
        CASE WHEN TG_TABLE_NAME = 'messages' THEN NEW.id END,
        CASE WHEN TG_TABLE_NAME = 'orders' THEN NEW.id END,
        CASE WHEN TG_TABLE_NAME IN ('orders', 'customers') THEN NEW.customer_id 
             WHEN TG_TABLE_NAME = 'messages' THEN (SELECT customer_id FROM conversations WHERE id = NEW.conversation_id) END
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create webhook triggers for important events
CREATE TRIGGER trigger_webhook_on_message
    AFTER INSERT OR UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION auto_trigger_webhooks();

CREATE TRIGGER trigger_webhook_on_order
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION auto_trigger_webhooks();

CREATE TRIGGER trigger_webhook_on_customer
    AFTER INSERT OR UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION auto_trigger_webhooks();

-- Add updated_at triggers
CREATE TRIGGER trigger_webhook_endpoints_updated_at
    BEFORE UPDATE ON webhook_endpoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_external_integrations_updated_at
    BEFORE UPDATE ON external_integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_webhook_event_templates_updated_at
    BEFORE UPDATE ON webhook_event_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS policies for new tables
ALTER TABLE webhook_endpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_message_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_event_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY webhook_endpoints_tenant_isolation ON webhook_endpoints
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY webhook_deliveries_tenant_isolation ON webhook_deliveries
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY external_integrations_tenant_isolation ON external_integrations
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY external_message_mappings_tenant_isolation ON external_message_mappings
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY api_rate_limits_tenant_isolation ON api_rate_limits
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY webhook_event_templates_tenant_isolation ON webhook_event_templates
    FOR ALL USING (distributor_id = get_current_distributor_id() OR distributor_id IS NULL OR is_service_role());

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON webhook_endpoints TO distributor_user;
GRANT SELECT ON webhook_deliveries TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON external_integrations TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON external_message_mappings TO distributor_user;
GRANT SELECT ON api_rate_limits TO distributor_user;
GRANT SELECT ON webhook_event_templates TO distributor_user;

GRANT EXECUTE ON FUNCTION trigger_webhook_delivery TO distributor_user;
GRANT EXECUTE ON FUNCTION check_rate_limit TO distributor_user;

-- Insert default webhook event templates
INSERT INTO webhook_event_templates (event_type, template_name, description, payload_template) VALUES
('message.created', 'Standard Message Created', 'Standard template for new message events', 
 '{"event": "message.created", "data": {"id": "{{message_id}}", "content": "{{content}}", "from_customer": "{{is_from_customer}}", "timestamp": "{{created_at}}"}}'),
('order.created', 'Standard Order Created', 'Standard template for new order events',
 '{"event": "order.created", "data": {"id": "{{order_id}}", "customer_id": "{{customer_id}}", "status": "{{status}}", "amount": "{{total_amount}}", "timestamp": "{{created_at}}"}}'),
('customer.created', 'Standard Customer Created', 'Standard template for new customer events',
 '{"event": "customer.created", "data": {"id": "{{customer_id}}", "name": "{{business_name}}", "status": "{{status}}", "timestamp": "{{created_at}}"}}');

-- Add comments for documentation
COMMENT ON TABLE webhook_endpoints IS 'Webhook endpoint configurations for external system integrations';
COMMENT ON TABLE webhook_deliveries IS 'Webhook delivery attempts and logs with retry logic';
COMMENT ON TABLE external_integrations IS 'External system integrations (WhatsApp, SMS, Email providers)';
COMMENT ON TABLE external_message_mappings IS 'Mapping between external and internal message identifiers';
COMMENT ON TABLE api_rate_limits IS 'API rate limiting configuration and tracking';
COMMENT ON TABLE webhook_event_templates IS 'Reusable templates for webhook event payloads';

COMMENT ON FUNCTION trigger_webhook_delivery IS 'Triggers webhook deliveries for specified events';
COMMENT ON FUNCTION check_rate_limit IS 'Checks and enforces API rate limits';
COMMENT ON FUNCTION process_webhook_delivery_queue IS 'Processes pending webhook deliveries from queue';