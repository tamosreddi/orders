-- Create AI and support tables
-- Tables for AI agent tracking, future products catalog, and message templates

-- AI responses tracking table
CREATE TABLE ai_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Agent information
    agent_type TEXT NOT NULL CHECK (agent_type IN ('ORDER_PROCESSING', 'CUSTOMER_SUPPORT', 'MESSAGE_ANALYSIS', 'CONTEXT_MANAGER')),
    agent_version TEXT DEFAULT 'v1.0', -- Track agent version for improvements
    
    -- Response data
    response_content TEXT NOT NULL, -- Generated response text
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1), -- 0.00 to 1.00
    processing_time INTEGER, -- Processing time in milliseconds
    
    -- Extracted structured data (JSON)
    extracted_data JSONB, -- Structured data extracted by agent (orders, intents, etc.)
    
    -- Response metadata
    tokens_used INTEGER, -- OpenAI tokens consumed
    model_used TEXT DEFAULT 'gpt-4', -- AI model used
    prompt_version TEXT, -- Version of prompt used
    
    -- Quality tracking
    human_feedback TEXT CHECK (human_feedback IN ('HELPFUL', 'PARTIALLY_HELPFUL', 'NOT_HELPFUL')),
    human_feedback_notes TEXT,
    was_used BOOLEAN DEFAULT FALSE, -- Whether the AI response was actually used
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Message templates for AI responses
CREATE TABLE message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    template_content TEXT NOT NULL,
    
    -- Template metadata
    agent_type TEXT CHECK (agent_type IN ('ORDER_PROCESSING', 'CUSTOMER_SUPPORT', 'MESSAGE_ANALYSIS', 'CONTEXT_MANAGER')),
    category TEXT, -- greeting, order_confirmation, error_handling, etc.
    language TEXT DEFAULT 'en',
    
    -- Template variables (JSON schema)
    variables JSONB DEFAULT '[]'::jsonb, -- List of variables that can be substituted
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Future products catalog table (for when product matching is implemented)
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    sku TEXT UNIQUE, -- Stock Keeping Unit
    description TEXT,
    
    -- Product details
    category TEXT,
    unit TEXT NOT NULL, -- kg, units, boxes, liters, etc.
    unit_price DECIMAL(10,2),
    
    -- AI matching
    aliases JSONB DEFAULT '[]'::jsonb, -- Alternative names for AI matching
    keywords JSONB DEFAULT '[]'::jsonb, -- Keywords for search/matching
    
    -- Inventory (basic)
    in_stock BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI training data table (for improving AI performance)
CREATE TABLE ai_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Input data
    input_text TEXT NOT NULL, -- Original message text
    input_context JSONB, -- Additional context (customer history, etc.)
    
    -- Expected output
    expected_output JSONB NOT NULL, -- What the AI should have extracted/generated
    expected_confidence DECIMAL(3,2), -- Expected confidence level
    
    -- Actual AI output (for comparison)
    actual_output JSONB,
    actual_confidence DECIMAL(3,2),
    
    -- Training metadata
    data_source TEXT CHECK (data_source IN ('MANUAL_ENTRY', 'CORRECTED_AI_OUTPUT', 'EXPERT_REVIEW')),
    quality_score INTEGER CHECK (quality_score >= 1 AND quality_score <= 5), -- 1-5 quality rating
    
    -- Usage in training
    used_in_training BOOLEAN DEFAULT FALSE,
    training_batch TEXT, -- Which training batch this was used in
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_ai_responses_message ON ai_responses(message_id);
CREATE INDEX idx_ai_responses_agent_type ON ai_responses(agent_type);
CREATE INDEX idx_ai_responses_created_at ON ai_responses(created_at DESC);
CREATE INDEX idx_ai_responses_confidence ON ai_responses(confidence);

CREATE INDEX idx_message_templates_agent_type ON message_templates(agent_type);
CREATE INDEX idx_message_templates_category ON message_templates(category);
CREATE INDEX idx_message_templates_active ON message_templates(active) WHERE active = TRUE;

CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_active ON products(active) WHERE active = TRUE;

-- GIN indexes for JSONB fields
CREATE INDEX idx_products_aliases_gin ON products USING GIN (aliases);
CREATE INDEX idx_products_keywords_gin ON products USING GIN (keywords);
CREATE INDEX idx_ai_responses_extracted_data_gin ON ai_responses USING GIN (extracted_data);

-- Add comments for documentation
COMMENT ON TABLE ai_responses IS 'Tracks AI agent responses and performance for continuous improvement';
COMMENT ON TABLE message_templates IS 'Reusable message templates for AI agents';
COMMENT ON TABLE products IS 'Future products catalog for AI product matching';
COMMENT ON TABLE ai_training_data IS 'Training data for improving AI agent performance';

COMMENT ON COLUMN ai_responses.agent_type IS 'Type of AI agent that generated response';
COMMENT ON COLUMN ai_responses.extracted_data IS 'Structured data extracted by AI (orders, intents, etc.)';
COMMENT ON COLUMN ai_responses.human_feedback IS 'Human quality rating of AI response';
COMMENT ON COLUMN products.aliases IS 'Alternative product names for AI matching';
COMMENT ON COLUMN products.keywords IS 'Search keywords for product identification';