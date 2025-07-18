-- Create additional indexes for optimal performance
-- These indexes support complex queries for the Messages, Orders, and Customers pages

-- Composite indexes for common query patterns

-- Customers page filtering and sorting
CREATE INDEX IF NOT EXISTS idx_customers_status_last_ordered ON customers(status, last_ordered_date DESC);
CREATE INDEX IF NOT EXISTS idx_customers_invitation_joined ON customers(invitation_status, joined_date DESC);
CREATE INDEX IF NOT EXISTS idx_customers_search_text ON customers USING gin(to_tsvector('english', business_name || ' ' || COALESCE(contact_person_name, '') || ' ' || customer_code));

-- Messages page conversation list (sorted by last message)
CREATE INDEX IF NOT EXISTS idx_conversations_customer_last_message ON conversations(customer_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_status_last_message ON conversations(status, last_message_at DESC) WHERE status = 'ACTIVE';

-- Message thread queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at ASC); -- For chronological message loading
CREATE INDEX IF NOT EXISTS idx_messages_unprocessed_ai ON messages(ai_processed, created_at DESC) WHERE ai_processed = FALSE; -- For AI processing queue

-- Orders page filtering and sorting
CREATE INDEX IF NOT EXISTS idx_orders_status_received_date ON orders(status, received_date DESC);
CREATE INDEX IF NOT EXISTS idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_channel_date ON orders(channel, received_date DESC);

-- Order products for order detail views
CREATE INDEX IF NOT EXISTS idx_order_products_order_line_order ON order_products(order_id, line_order ASC); -- For ordered product display

-- AI performance indexes
CREATE INDEX IF NOT EXISTS idx_ai_responses_agent_created ON ai_responses(agent_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_responses_quality ON ai_responses(human_feedback, confidence DESC) WHERE human_feedback IS NOT NULL;

-- Search and filtering indexes
CREATE INDEX IF NOT EXISTS idx_orders_search_text ON orders USING gin(to_tsvector('english', 
    COALESCE(additional_comment, '') || ' ' || 
    COALESCE(whatsapp_message, '') || ' ' || 
    COALESCE(external_order_id, '')
));

CREATE INDEX IF NOT EXISTS idx_messages_search_text ON messages USING gin(to_tsvector('english', content));

-- Performance indexes for real-time features
CREATE INDEX IF NOT EXISTS idx_conversations_unread_sorted ON conversations(unread_count DESC, last_message_at DESC) WHERE unread_count > 0;
CREATE INDEX IF NOT EXISTS idx_messages_recent_from_customer ON messages(is_from_customer, created_at DESC) WHERE is_from_customer = TRUE;

-- Partial indexes for specific statuses (smaller, faster)
CREATE INDEX IF NOT EXISTS idx_orders_pending ON orders(received_date DESC) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_orders_review ON orders(received_date DESC) WHERE status = 'REVIEW';
CREATE INDEX IF NOT EXISTS idx_orders_confirmed ON orders(received_date DESC) WHERE status = 'CONFIRMED';

-- Customer activity tracking
CREATE INDEX IF NOT EXISTS idx_customers_recent_activity ON customers(last_ordered_date DESC) WHERE last_ordered_date IS NOT NULL;

-- AI agent efficiency indexes
CREATE INDEX IF NOT EXISTS idx_ai_responses_processing_time ON ai_responses(agent_type, processing_time) WHERE processing_time IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_messages_ai_confidence ON messages(ai_confidence DESC) WHERE ai_confidence IS NOT NULL;

-- Foreign key performance (if not already covered)
CREATE INDEX IF NOT EXISTS idx_customer_label_assignments_label ON customer_label_assignments(label_id);
CREATE INDEX IF NOT EXISTS idx_messages_reply_to ON messages(reply_to_message_id) WHERE reply_to_message_id IS NOT NULL;

-- Add comments for documentation
COMMENT ON INDEX idx_customers_search_text IS 'Full-text search across customer name, contact person, and code';
COMMENT ON INDEX idx_orders_search_text IS 'Full-text search across order comments and messages';
COMMENT ON INDEX idx_messages_search_text IS 'Full-text search across message content';
COMMENT ON INDEX idx_conversations_customer_last_message IS 'Optimizes conversation list sorting by last message';
COMMENT ON INDEX idx_messages_conversation_created IS 'Optimizes chronological message loading in threads';
COMMENT ON INDEX idx_ai_responses_processing_time IS 'Tracks AI agent performance metrics';