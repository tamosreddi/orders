-- Create messages table
-- Core table for storing all messages from the Messages interface
-- Supports text, images, audio, files, and order context messages

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message content
    content TEXT NOT NULL, -- Message.content
    is_from_customer BOOLEAN NOT NULL, -- Message.isFromCustomer
    
    -- Message type and status
    message_type TEXT CHECK (message_type IN ('TEXT', 'IMAGE', 'AUDIO', 'FILE', 'ORDER_CONTEXT')) DEFAULT 'TEXT',
    status TEXT CHECK (status IN ('SENT', 'DELIVERED', 'READ')) DEFAULT 'SENT', -- Message.status
    
    -- File attachments (JSON array of file objects)
    attachments JSONB DEFAULT '[]'::jsonb, -- Message attachments
    
    -- AI processing fields
    ai_processed BOOLEAN DEFAULT FALSE,
    ai_confidence DECIMAL(3,2), -- 0.00 to 1.00 confidence score
    ai_extracted_intent TEXT, -- AI-detected intent (order, question, complaint, etc.)
    ai_extracted_products JSONB, -- AI-extracted product information
    ai_suggested_responses JSONB DEFAULT '[]'::jsonb, -- Message.aiSuggestions
    
    -- Order context (for messages that reference orders)
    order_context_id UUID, -- References orders.id (soft reference, can be null)
    
    -- Message metadata
    thread_position INTEGER, -- Position in conversation thread
    reply_to_message_id UUID REFERENCES messages(id), -- For threaded replies
    
    -- External system references
    external_message_id TEXT, -- WhatsApp/SMS/Email provider message ID
    external_metadata JSONB, -- Provider-specific metadata
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_is_from_customer ON messages(is_from_customer);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_ai_processed ON messages(ai_processed) WHERE ai_processed = FALSE;
CREATE INDEX idx_messages_message_type ON messages(message_type);
CREATE INDEX idx_messages_order_context ON messages(order_context_id) WHERE order_context_id IS NOT NULL;

-- GIN index for JSONB fields (for AI data querying)
CREATE INDEX idx_messages_attachments_gin ON messages USING GIN (attachments);
CREATE INDEX idx_messages_ai_products_gin ON messages USING GIN (ai_extracted_products);
CREATE INDEX idx_messages_ai_responses_gin ON messages USING GIN (ai_suggested_responses);

-- Add comments for documentation
COMMENT ON TABLE messages IS 'Core messages table supporting Message TypeScript interface';
COMMENT ON COLUMN messages.content IS 'Message text content (Message.content)';
COMMENT ON COLUMN messages.is_from_customer IS 'True if message sent by customer (Message.isFromCustomer)';
COMMENT ON COLUMN messages.status IS 'Delivery status: SENT, DELIVERED, READ (Message.status)';
COMMENT ON COLUMN messages.attachments IS 'JSON array of file attachments';
COMMENT ON COLUMN messages.ai_confidence IS 'AI processing confidence score (0.00 to 1.00)';
COMMENT ON COLUMN messages.ai_suggested_responses IS 'AI-generated response suggestions (Message.aiSuggestions)';
COMMENT ON COLUMN messages.order_context_id IS 'Soft reference to related order for context cards';
COMMENT ON COLUMN messages.external_message_id IS 'Provider-specific message identifier';