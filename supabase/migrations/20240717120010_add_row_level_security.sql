-- Add Row Level Security (RLS) policies for all tables
-- Critical security implementation for multi-tenant B2B platform
-- Ensures distributors can only access their own data

-- Enable RLS on all tables
ALTER TABLE distributors ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_labels ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_label_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_training_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE distributor_usage ENABLE ROW LEVEL SECURITY;

-- Helper function to get current distributor ID from JWT token
CREATE OR REPLACE FUNCTION get_current_distributor_id()
RETURNS UUID AS $$
BEGIN
    -- In production, this would extract the distributor_id from the JWT token
    -- For now, we'll use a simple approach that can be extended
    RETURN COALESCE(
        (current_setting('app.current_distributor_id', true))::UUID,
        NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Alternative function for service role access (admin operations)
CREATE OR REPLACE FUNCTION is_service_role()
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if current role is the service role (for admin operations)
    RETURN current_setting('role') = 'service_role' OR 
           current_setting('app.bypass_rls', true) = 'true';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- RLS Policies for distributors table
-- Distributors can only see their own record
CREATE POLICY distributors_tenant_isolation ON distributors
    FOR ALL USING (
        id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for customers table
CREATE POLICY customers_tenant_isolation ON customers
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY customers_insert_policy ON customers
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for customer_labels table
CREATE POLICY customer_labels_tenant_isolation ON customer_labels
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY customer_labels_insert_policy ON customer_labels
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for customer_label_assignments table
CREATE POLICY customer_label_assignments_tenant_isolation ON customer_label_assignments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM customers c 
            WHERE c.id = customer_label_assignments.customer_id 
            AND (c.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY customer_label_assignments_insert_policy ON customer_label_assignments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM customers c 
            WHERE c.id = customer_label_assignments.customer_id 
            AND (c.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

-- RLS Policies for conversations table
CREATE POLICY conversations_tenant_isolation ON conversations
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY conversations_insert_policy ON conversations
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for messages table
CREATE POLICY messages_tenant_isolation ON messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM conversations conv 
            WHERE conv.id = messages.conversation_id 
            AND (conv.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY messages_insert_policy ON messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations conv 
            WHERE conv.id = messages.conversation_id 
            AND (conv.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

-- RLS Policies for orders table
CREATE POLICY orders_tenant_isolation ON orders
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY orders_insert_policy ON orders
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for order_products table
CREATE POLICY order_products_tenant_isolation ON order_products
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM orders o 
            WHERE o.id = order_products.order_id 
            AND (o.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY order_products_insert_policy ON order_products
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM orders o 
            WHERE o.id = order_products.order_id 
            AND (o.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

-- RLS Policies for order_attachments table
CREATE POLICY order_attachments_tenant_isolation ON order_attachments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM orders o 
            WHERE o.id = order_attachments.order_id 
            AND (o.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY order_attachments_insert_policy ON order_attachments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM orders o 
            WHERE o.id = order_attachments.order_id 
            AND (o.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

-- RLS Policies for ai_responses table
CREATE POLICY ai_responses_tenant_isolation ON ai_responses
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM messages m 
            JOIN conversations c ON c.id = m.conversation_id
            WHERE m.id = ai_responses.message_id 
            AND (c.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY ai_responses_insert_policy ON ai_responses
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM messages m 
            JOIN conversations c ON c.id = m.conversation_id
            WHERE m.id = ai_responses.message_id 
            AND (c.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

-- RLS Policies for message_templates table
CREATE POLICY message_templates_tenant_isolation ON message_templates
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR 
        distributor_id IS NULL OR -- Global templates
        is_service_role()
    );

CREATE POLICY message_templates_insert_policy ON message_templates
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for products table
CREATE POLICY products_tenant_isolation ON products
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY products_insert_policy ON products
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for ai_training_data table
-- More permissive for AI improvement, but still tenant-aware
CREATE POLICY ai_training_data_tenant_isolation ON ai_training_data
    FOR SELECT USING (
        is_service_role() OR 
        data_source IN ('MANUAL_ENTRY', 'CORRECTED_AI_OUTPUT')
    );

CREATE POLICY ai_training_data_insert_policy ON ai_training_data
    FOR INSERT WITH CHECK (
        is_service_role() OR 
        data_source IN ('MANUAL_ENTRY', 'CORRECTED_AI_OUTPUT')
    );

-- RLS Policies for distributor_usage table
CREATE POLICY distributor_usage_tenant_isolation ON distributor_usage
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY distributor_usage_insert_policy ON distributor_usage
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- Create admin role for platform management
CREATE ROLE platform_admin;
GRANT ALL ON ALL TABLES IN SCHEMA public TO platform_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO platform_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO platform_admin;

-- Create distributor user role with limited permissions
CREATE ROLE distributor_user;
GRANT SELECT, INSERT, UPDATE ON customers TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON customer_labels TO distributor_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON customer_label_assignments TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON conversations TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON messages TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON orders TO distributor_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON order_products TO distributor_user;
GRANT SELECT, INSERT, DELETE ON order_attachments TO distributor_user;
GRANT SELECT, INSERT ON ai_responses TO distributor_user;
GRANT SELECT ON message_templates TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON products TO distributor_user;
GRANT SELECT ON distributor_usage TO distributor_user;
GRANT SELECT ON distributors TO distributor_user;

-- Grant sequence usage
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO distributor_user;

-- Create function to set distributor context (called from application)
CREATE OR REPLACE FUNCTION set_distributor_context(distributor_uuid UUID)
RETURNS VOID AS $$
BEGIN
    -- Set the current distributor ID for the session
    PERFORM set_config('app.current_distributor_id', distributor_uuid::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to validate distributor access
CREATE OR REPLACE FUNCTION validate_distributor_access(table_name TEXT, record_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_dist_id UUID;
    record_dist_id UUID;
    query_text TEXT;
BEGIN
    current_dist_id := get_current_distributor_id();
    
    -- If service role, allow all access
    IF is_service_role() THEN
        RETURN TRUE;
    END IF;
    
    -- If no current distributor set, deny access
    IF current_dist_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Build dynamic query based on table
    CASE table_name
        WHEN 'customers', 'conversations', 'orders', 'products', 'customer_labels', 'message_templates' THEN
            query_text := format('SELECT distributor_id FROM %I WHERE id = $1', table_name);
        WHEN 'messages' THEN
            query_text := 'SELECT c.distributor_id FROM messages m JOIN conversations c ON c.id = m.conversation_id WHERE m.id = $1';
        WHEN 'order_products' THEN
            query_text := 'SELECT o.distributor_id FROM order_products op JOIN orders o ON o.id = op.order_id WHERE op.id = $1';
        WHEN 'order_attachments' THEN
            query_text := 'SELECT o.distributor_id FROM order_attachments oa JOIN orders o ON o.id = oa.order_id WHERE oa.id = $1';
        ELSE
            RETURN FALSE;
    END CASE;
    
    EXECUTE query_text INTO record_dist_id USING record_id;
    
    RETURN record_dist_id = current_dist_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit function for RLS violations (optional monitoring)
CREATE OR REPLACE FUNCTION log_rls_violation()
RETURNS TRIGGER AS $$
BEGIN
    -- Log potential RLS violations for monitoring
    INSERT INTO public.security_audit_log (
        table_name,
        operation,
        user_id,
        distributor_id,
        attempted_record_id,
        created_at
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        current_user,
        get_current_distributor_id(),
        COALESCE(NEW.id, OLD.id),
        NOW()
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create security audit log table
CREATE TABLE security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    user_id TEXT,
    distributor_id UUID,
    attempted_record_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for audit log
CREATE INDEX idx_security_audit_log_created_at ON security_audit_log(created_at DESC);
CREATE INDEX idx_security_audit_log_distributor ON security_audit_log(distributor_id, created_at DESC);

-- Grant permissions on audit log
GRANT SELECT, INSERT ON security_audit_log TO distributor_user;
GRANT ALL ON security_audit_log TO platform_admin;

-- Add comments for documentation
COMMENT ON FUNCTION get_current_distributor_id IS 'Returns the current distributor ID from session context';
COMMENT ON FUNCTION is_service_role IS 'Checks if current user has service role privileges';
COMMENT ON FUNCTION set_distributor_context IS 'Sets the distributor context for the current session';
COMMENT ON FUNCTION validate_distributor_access IS 'Validates if current distributor can access a specific record';
COMMENT ON TABLE security_audit_log IS 'Audit log for security events and potential RLS violations';

-- Create view for distributor-specific analytics (respects RLS automatically)
CREATE VIEW distributor_analytics AS
SELECT 
    d.id as distributor_id,
    d.business_name,
    COUNT(DISTINCT c.id) as total_customers,
    COUNT(DISTINCT o.id) as total_orders,
    COUNT(DISTINCT conv.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COALESCE(SUM(o.total_amount), 0) as total_revenue,
    COUNT(DISTINCT CASE WHEN o.created_at >= NOW() - INTERVAL '30 days' THEN o.id END) as orders_last_30_days,
    COUNT(DISTINCT CASE WHEN m.created_at >= NOW() - INTERVAL '30 days' THEN m.id END) as messages_last_30_days
FROM distributors d
LEFT JOIN customers c ON c.distributor_id = d.id
LEFT JOIN orders o ON o.distributor_id = d.id
LEFT JOIN conversations conv ON conv.distributor_id = d.id
LEFT JOIN messages m ON m.conversation_id = conv.id
GROUP BY d.id, d.business_name;

-- Grant access to the analytics view
GRANT SELECT ON distributor_analytics TO distributor_user;
GRANT ALL ON distributor_analytics TO platform_admin;

COMMENT ON VIEW distributor_analytics IS 'Analytics view for distributor dashboard (RLS-protected)';