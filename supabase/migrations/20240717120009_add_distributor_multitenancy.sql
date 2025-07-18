-- Add distributor multi-tenancy support
-- This migration adds the critical distributor table and multi-tenant architecture
-- Required for B2B platform where multiple distributors use the same system

-- Create distributors table (the tenant table)
CREATE TABLE distributors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Business information
    business_name TEXT NOT NULL,
    domain TEXT UNIQUE, -- distributor.example.com
    subdomain TEXT UNIQUE, -- subdomain for multi-tenant access
    
    -- Authentication & API
    api_key_hash TEXT, -- Hashed API key for external integrations
    webhook_secret TEXT, -- Secret for webhook verification
    
    -- Subscription & billing
    subscription_tier TEXT CHECK (subscription_tier IN ('FREE', 'BASIC', 'PREMIUM', 'ENTERPRISE')) DEFAULT 'FREE',
    subscription_status TEXT CHECK (subscription_status IN ('ACTIVE', 'SUSPENDED', 'CANCELLED')) DEFAULT 'ACTIVE',
    billing_email TEXT,
    
    -- Contact information
    contact_name TEXT,
    contact_email TEXT NOT NULL,
    contact_phone TEXT,
    address TEXT,
    
    -- Platform settings
    timezone TEXT DEFAULT 'UTC',
    locale TEXT DEFAULT 'en',
    currency TEXT DEFAULT 'USD',
    
    -- AI settings
    ai_enabled BOOLEAN DEFAULT TRUE,
    ai_model_preference TEXT DEFAULT 'gpt-4',
    ai_confidence_threshold DECIMAL(3,2) DEFAULT 0.8,
    monthly_ai_budget_usd DECIMAL(10,2) DEFAULT 100.00,
    
    -- Status and metadata
    status TEXT CHECK (status IN ('ACTIVE', 'INACTIVE', 'PENDING_SETUP')) DEFAULT 'PENDING_SETUP',
    onboarding_completed BOOLEAN DEFAULT FALSE,
    
    -- Usage limits (based on subscription tier)
    max_customers INTEGER,
    max_monthly_messages INTEGER,
    max_monthly_ai_requests INTEGER,
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add distributor_id to existing tables
ALTER TABLE customers ADD COLUMN distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE;
ALTER TABLE customer_labels ADD COLUMN distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE;
ALTER TABLE conversations ADD COLUMN distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE;
ALTER TABLE orders ADD COLUMN distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE;
ALTER TABLE products ADD COLUMN distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE;
ALTER TABLE message_templates ADD COLUMN distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE;

-- Create distributor usage tracking table
CREATE TABLE distributor_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Usage period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Usage metrics
    customers_count INTEGER DEFAULT 0,
    messages_count INTEGER DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    ai_requests_count INTEGER DEFAULT 0,
    ai_tokens_used INTEGER DEFAULT 0,
    ai_cost_usd DECIMAL(10,4) DEFAULT 0,
    
    -- Calculated fields
    storage_used_mb INTEGER DEFAULT 0,
    bandwidth_used_mb INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one record per distributor per period
    UNIQUE(distributor_id, period_start, period_end)
);

-- Create indexes for performance
CREATE INDEX idx_distributors_domain ON distributors(domain);
CREATE INDEX idx_distributors_subdomain ON distributors(subdomain);
CREATE INDEX idx_distributors_status ON distributors(status, subscription_status);
CREATE INDEX idx_distributors_subscription ON distributors(subscription_tier, subscription_status);

-- Multi-tenant indexes (critical for performance)
CREATE INDEX idx_customers_distributor ON customers(distributor_id);
CREATE INDEX idx_customer_labels_distributor ON customer_labels(distributor_id);
CREATE INDEX idx_conversations_distributor ON conversations(distributor_id);
CREATE INDEX idx_orders_distributor ON orders(distributor_id);
CREATE INDEX idx_products_distributor ON products(distributor_id);
CREATE INDEX idx_message_templates_distributor ON message_templates(distributor_id);

CREATE INDEX idx_distributor_usage_period ON distributor_usage(distributor_id, period_start DESC);

-- Composite indexes for tenant-specific queries
CREATE INDEX idx_customers_distributor_status ON customers(distributor_id, status);
CREATE INDEX idx_orders_distributor_status ON orders(distributor_id, status);
CREATE INDEX idx_conversations_distributor_active ON conversations(distributor_id, status) WHERE status = 'ACTIVE';

-- Update existing unique constraints to include distributor_id where appropriate
DROP INDEX IF EXISTS idx_customers_code;
CREATE UNIQUE INDEX idx_customers_distributor_code ON customers(distributor_id, customer_code);

-- Update conversations unique constraint
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_customer_id_channel_key;
ALTER TABLE conversations ADD CONSTRAINT conversations_distributor_customer_channel_unique 
    UNIQUE(distributor_id, customer_id, channel);

-- Insert a default distributor for existing data (migration safety)
INSERT INTO distributors (
    id,
    business_name,
    contact_email,
    status,
    onboarding_completed
) VALUES (
    gen_random_uuid(),
    'Default Distributor',
    'admin@example.com',
    'ACTIVE',
    TRUE
) ON CONFLICT DO NOTHING;

-- Update existing records to use the default distributor
UPDATE customers SET distributor_id = (SELECT id FROM distributors LIMIT 1) WHERE distributor_id IS NULL;
UPDATE customer_labels SET distributor_id = (SELECT id FROM distributors LIMIT 1) WHERE distributor_id IS NULL;
UPDATE conversations SET distributor_id = (SELECT id FROM distributors LIMIT 1) WHERE distributor_id IS NULL;
UPDATE orders SET distributor_id = (SELECT id FROM distributors LIMIT 1) WHERE distributor_id IS NULL;
UPDATE products SET distributor_id = (SELECT id FROM distributors LIMIT 1) WHERE distributor_id IS NULL;
UPDATE message_templates SET distributor_id = (SELECT id FROM distributors LIMIT 1) WHERE distributor_id IS NULL;

-- Make distributor_id NOT NULL after migration
ALTER TABLE customers ALTER COLUMN distributor_id SET NOT NULL;
ALTER TABLE customer_labels ALTER COLUMN distributor_id SET NOT NULL;
ALTER TABLE conversations ALTER COLUMN distributor_id SET NOT NULL;
ALTER TABLE orders ALTER COLUMN distributor_id SET NOT NULL;
ALTER TABLE products ALTER COLUMN distributor_id SET NOT NULL;
ALTER TABLE message_templates ALTER COLUMN distributor_id SET NOT NULL;

-- Create function to check subscription limits
CREATE OR REPLACE FUNCTION check_subscription_limits()
RETURNS TRIGGER AS $$
DECLARE
    dist_record distributors%ROWTYPE;
    current_count INTEGER;
BEGIN
    -- Get distributor record
    SELECT * INTO dist_record FROM distributors WHERE id = NEW.distributor_id;
    
    -- Check customer limit
    IF TG_TABLE_NAME = 'customers' AND dist_record.max_customers IS NOT NULL THEN
        SELECT COUNT(*) INTO current_count FROM customers WHERE distributor_id = NEW.distributor_id;
        IF current_count >= dist_record.max_customers THEN
            RAISE EXCEPTION 'Customer limit reached for subscription tier: %', dist_record.subscription_tier;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply subscription limit triggers
CREATE TRIGGER trigger_check_customer_limits
    BEFORE INSERT ON customers
    FOR EACH ROW EXECUTE FUNCTION check_subscription_limits();

-- Update triggers to maintain distributor isolation
CREATE OR REPLACE FUNCTION update_distributor_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- Update current period usage when records are added
    INSERT INTO distributor_usage (
        distributor_id,
        period_start,
        period_end,
        customers_count,
        messages_count,
        orders_count
    ) VALUES (
        NEW.distributor_id,
        DATE_TRUNC('month', NOW())::DATE,
        (DATE_TRUNC('month', NOW()) + INTERVAL '1 month - 1 day')::DATE,
        CASE WHEN TG_TABLE_NAME = 'customers' THEN 1 ELSE 0 END,
        CASE WHEN TG_TABLE_NAME = 'messages' THEN 1 ELSE 0 END,
        CASE WHEN TG_TABLE_NAME = 'orders' THEN 1 ELSE 0 END
    ) ON CONFLICT (distributor_id, period_start, period_end) DO UPDATE SET
        customers_count = distributor_usage.customers_count + 
            CASE WHEN TG_TABLE_NAME = 'customers' THEN 1 ELSE 0 END,
        messages_count = distributor_usage.messages_count + 
            CASE WHEN TG_TABLE_NAME = 'messages' THEN 1 ELSE 0 END,
        orders_count = distributor_usage.orders_count + 
            CASE WHEN TG_TABLE_NAME = 'orders' THEN 1 ELSE 0 END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at trigger for distributors
CREATE TRIGGER trigger_distributors_updated_at
    BEFORE UPDATE ON distributors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE distributors IS 'Multi-tenant distributor/organization table for B2B platform';
COMMENT ON TABLE distributor_usage IS 'Tracks usage metrics per distributor for billing and limits';
COMMENT ON COLUMN distributors.subscription_tier IS 'Subscription level determining feature access and limits';
COMMENT ON COLUMN distributors.ai_confidence_threshold IS 'Minimum AI confidence required for auto-processing orders';
COMMENT ON COLUMN distributors.monthly_ai_budget_usd IS 'Monthly budget limit for AI API usage';
COMMENT ON FUNCTION check_subscription_limits IS 'Enforces subscription tier limits on resource creation';