-- Create conversations table
-- Groups messages by customer and channel for the Messages page
-- Each customer can have one conversation per channel (WhatsApp, SMS, Email)

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Channel information
    channel TEXT NOT NULL CHECK (channel IN ('WHATSAPP', 'SMS', 'EMAIL')),
    
    -- Conversation status
    status TEXT CHECK (status IN ('ACTIVE', 'ARCHIVED')) DEFAULT 'ACTIVE',
    
    -- Conversation metadata
    last_message_at TIMESTAMPTZ, -- Timestamp of most recent message
    unread_count INTEGER DEFAULT 0, -- Number of unread messages from customer
    
    -- AI processing metadata
    ai_context_summary TEXT, -- AI-generated summary of conversation context
    ai_last_processed_at TIMESTAMPTZ, -- When AI last analyzed this conversation
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one conversation per customer per channel
    UNIQUE(customer_id, channel)
);

-- Create indexes for performance
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_channel ON conversations(channel);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX idx_conversations_unread ON conversations(unread_count) WHERE unread_count > 0;

-- Add comments for documentation
COMMENT ON TABLE conversations IS 'Groups messages by customer and channel for Messages page interface';
COMMENT ON COLUMN conversations.channel IS 'Communication channel: WHATSAPP, SMS, or EMAIL';
COMMENT ON COLUMN conversations.last_message_at IS 'Timestamp of most recent message for sorting';
COMMENT ON COLUMN conversations.unread_count IS 'Number of unread messages from customer';
COMMENT ON COLUMN conversations.ai_context_summary IS 'AI-generated conversation context summary';
COMMENT ON CONSTRAINT conversations_customer_id_channel_key ON conversations IS 'Ensures one conversation per customer per channel';