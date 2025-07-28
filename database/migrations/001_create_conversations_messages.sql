-- Migration: Create conversations and messages tables for WhatsApp integration
-- This creates the necessary tables for the messaging system

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
  channel TEXT NOT NULL CHECK (channel IN ('WHATSAPP', 'SMS', 'EMAIL')),
  status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ARCHIVED', 'CLOSED')),
  last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  unread_count INTEGER NOT NULL DEFAULT 0,
  ai_context_summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  is_from_customer BOOLEAN NOT NULL DEFAULT TRUE,
  message_type TEXT NOT NULL DEFAULT 'TEXT' CHECK (message_type IN ('TEXT', 'IMAGE', 'AUDIO', 'FILE', 'ORDER_CONTEXT')),
  status TEXT NOT NULL DEFAULT 'SENT' CHECK (status IN ('SENT', 'DELIVERED', 'READ', 'FAILED', 'RECEIVED')),
  attachments JSONB DEFAULT '[]'::jsonb,
  
  -- AI processing fields
  ai_processed BOOLEAN DEFAULT FALSE,
  ai_confidence DECIMAL(3,2), -- 0.00 to 1.00
  ai_extracted_intent TEXT,
  ai_extracted_products JSONB,
  ai_suggested_responses JSONB,
  
  -- External system integration
  external_message_id TEXT, -- For Twilio MessageSid, etc.
  order_context_id UUID, -- Link to order if message is order-related
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_customer_id 
  ON conversations(customer_id);

CREATE INDEX IF NOT EXISTS idx_conversations_distributor_id 
  ON conversations(distributor_id);

CREATE INDEX IF NOT EXISTS idx_conversations_channel 
  ON conversations(channel);

CREATE INDEX IF NOT EXISTS idx_conversations_last_message_at 
  ON conversations(last_message_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
  ON messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_created_at 
  ON messages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_external_id 
  ON messages(external_message_id) WHERE external_message_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_ai_processed 
  ON messages(ai_processed) WHERE ai_processed = TRUE;

-- Add foreign key for conversations last message (self-referencing)
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS last_message_id UUID REFERENCES messages(id);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER IF NOT EXISTS update_conversations_updated_at 
  BEFORE UPDATE ON conversations 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_messages_updated_at 
  BEFORE UPDATE ON messages 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies for conversations
CREATE POLICY IF NOT EXISTS "Distributors can access their own conversations" 
  ON conversations FOR ALL 
  USING (distributor_id = current_setting('app.current_distributor_id')::uuid);

-- RLS Policies for messages (through conversation relationship)
CREATE POLICY IF NOT EXISTS "Distributors can access messages through conversations" 
  ON messages FOR ALL 
  USING (
    conversation_id IN (
      SELECT id FROM conversations 
      WHERE distributor_id = current_setting('app.current_distributor_id')::uuid
    )
  );

-- Grant permissions to authenticated users
GRANT ALL ON conversations TO authenticated;
GRANT ALL ON messages TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;