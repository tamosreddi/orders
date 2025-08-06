-- Add conversation order session management system
-- This migration creates tables and modifies existing tables to support
-- order collection sessions within conversations, implementing a state machine
-- for managing the order lifecycle from initial collection to consolidation

-- =====================================================
-- PART 1: Create conversation_order_sessions table
-- =====================================================

-- Create conversation_order_sessions table
-- This table manages order collection sessions within conversations
-- Each session represents a period where the agent is actively collecting order information
CREATE TABLE conversation_order_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Session state machine
    -- ACTIVE: Currently collecting order information
    -- COLLECTING: Actively gathering products/quantities
    -- REVIEWING: Order is being reviewed with customer
    -- CLOSED: Session completed (either confirmed or cancelled)
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'COLLECTING', 'REVIEWING', 'CLOSED')) DEFAULT 'ACTIVE',
    
    -- Session lifecycle timestamps
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    collecting_started_at TIMESTAMPTZ, -- When actual order collection began
    review_started_at TIMESTAMPTZ, -- When review phase started
    closed_at TIMESTAMPTZ, -- When session was closed
    
    -- Session outcome
    outcome TEXT CHECK (outcome IN ('CONFIRMED', 'CANCELLED', 'TIMEOUT', 'ABANDONED')),
    outcome_reason TEXT, -- Additional context for the outcome
    
    -- Consolidated order reference
    consolidated_order_id UUID, -- References orders(id) when order is consolidated
    
    -- Session metadata
    session_metadata JSONB DEFAULT '{}'::jsonb, -- Flexible metadata storage
    
    -- AI processing metadata
    ai_confidence_avg DECIMAL(3,2), -- Average AI confidence across session
    ai_interactions_count INTEGER DEFAULT 0, -- Number of AI interactions
    
    -- Session configuration
    auto_close_timeout_minutes INTEGER DEFAULT 30, -- Auto-close inactive sessions
    reminder_sent_at TIMESTAMPTZ, -- When reminder was sent for inactive session
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT, -- User/system that created the session
    closed_by TEXT -- User/system that closed the session
);

-- Create indexes for conversation_order_sessions
CREATE INDEX idx_order_sessions_conversation ON conversation_order_sessions(conversation_id);
CREATE INDEX idx_order_sessions_distributor ON conversation_order_sessions(distributor_id);
CREATE INDEX idx_order_sessions_status ON conversation_order_sessions(status);
CREATE INDEX idx_order_sessions_created_at ON conversation_order_sessions(created_at DESC);
CREATE INDEX idx_order_sessions_closed_at ON conversation_order_sessions(closed_at DESC) WHERE closed_at IS NOT NULL;
CREATE INDEX idx_order_sessions_consolidated_order ON conversation_order_sessions(consolidated_order_id) WHERE consolidated_order_id IS NOT NULL;
CREATE INDEX idx_order_sessions_active ON conversation_order_sessions(conversation_id, status) WHERE status IN ('ACTIVE', 'COLLECTING', 'REVIEWING');

-- Add comments for conversation_order_sessions
COMMENT ON TABLE conversation_order_sessions IS 'Manages order collection sessions within conversations, tracking state and grouping related messages';
COMMENT ON COLUMN conversation_order_sessions.status IS 'Session state: ACTIVE (initial), COLLECTING (gathering items), REVIEWING (confirming), CLOSED (completed)';
COMMENT ON COLUMN conversation_order_sessions.outcome IS 'Session outcome: CONFIRMED (order placed), CANCELLED (customer cancelled), TIMEOUT (auto-closed), ABANDONED (no activity)';
COMMENT ON COLUMN conversation_order_sessions.consolidated_order_id IS 'References the final consolidated order created from this session';
COMMENT ON COLUMN conversation_order_sessions.session_metadata IS 'Flexible JSON storage for session-specific data (e.g., customer preferences, special instructions)';
COMMENT ON COLUMN conversation_order_sessions.ai_confidence_avg IS 'Average AI confidence score across all interactions in this session';
COMMENT ON COLUMN conversation_order_sessions.auto_close_timeout_minutes IS 'Minutes of inactivity before session is automatically closed';

-- =====================================================
-- PART 2: Modify existing tables
-- =====================================================

-- Add order_session_id to messages table
ALTER TABLE messages 
ADD COLUMN order_session_id UUID REFERENCES conversation_order_sessions(id) ON DELETE SET NULL;

-- Create index for order_session_id in messages
CREATE INDEX idx_messages_order_session ON messages(order_session_id) WHERE order_session_id IS NOT NULL;

-- Add comment for new messages column
COMMENT ON COLUMN messages.order_session_id IS 'Links message to an order collection session for grouping related order messages';

-- Add columns to orders table
ALTER TABLE orders 
ADD COLUMN order_session_id UUID REFERENCES conversation_order_sessions(id) ON DELETE SET NULL,
ADD COLUMN is_consolidated BOOLEAN DEFAULT FALSE;

-- Create indexes for new orders columns
CREATE INDEX idx_orders_order_session ON orders(order_session_id) WHERE order_session_id IS NOT NULL;
CREATE INDEX idx_orders_is_consolidated ON orders(is_consolidated) WHERE is_consolidated = TRUE;

-- Add comments for new orders columns
COMMENT ON COLUMN orders.order_session_id IS 'Links order to the session that created it';
COMMENT ON COLUMN orders.is_consolidated IS 'True if this is the final consolidated order from a session';

-- =====================================================
-- PART 3: Create supporting tables
-- =====================================================

-- Create order_session_items table
-- Tracks individual items collected during a session before consolidation
CREATE TABLE order_session_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_session_id UUID NOT NULL REFERENCES conversation_order_sessions(id) ON DELETE CASCADE,
    
    -- Item details
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL, -- Store name in case product is deleted
    product_code TEXT, -- Store code for reference
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2),
    
    -- Item source tracking
    source_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    ai_extracted BOOLEAN DEFAULT FALSE,
    ai_confidence DECIMAL(3,2),
    
    -- Item status
    status TEXT CHECK (status IN ('PENDING', 'CONFIRMED', 'REMOVED')) DEFAULT 'PENDING',
    
    -- Timestamps
    added_at TIMESTAMPTZ DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    removed_at TIMESTAMPTZ,
    
    -- Metadata
    item_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for order_session_items
CREATE INDEX idx_session_items_session ON order_session_items(order_session_id);
CREATE INDEX idx_session_items_product ON order_session_items(product_id) WHERE product_id IS NOT NULL;
CREATE INDEX idx_session_items_status ON order_session_items(status);
CREATE INDEX idx_session_items_source_message ON order_session_items(source_message_id) WHERE source_message_id IS NOT NULL;

-- Add comments for order_session_items
COMMENT ON TABLE order_session_items IS 'Tracks individual items collected during an order session before consolidation';
COMMENT ON COLUMN order_session_items.product_name IS 'Stored product name to preserve history even if product is deleted';
COMMENT ON COLUMN order_session_items.ai_extracted IS 'True if item was extracted by AI from conversation';
COMMENT ON COLUMN order_session_items.status IS 'Item status: PENDING (not yet confirmed), CONFIRMED (customer approved), REMOVED (customer removed)';

-- =====================================================
-- PART 4: Create session event log table
-- =====================================================

-- Create order_session_events table
-- Audit trail for all events within an order session
CREATE TABLE order_session_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_session_id UUID NOT NULL REFERENCES conversation_order_sessions(id) ON DELETE CASCADE,
    
    -- Event details
    event_type TEXT NOT NULL CHECK (event_type IN (
        'SESSION_STARTED', 'SESSION_CLOSED', 
        'STATUS_CHANGED', 'ITEM_ADDED', 'ITEM_REMOVED', 'ITEM_MODIFIED',
        'REVIEW_REQUESTED', 'ORDER_CONFIRMED', 'ORDER_CANCELLED',
        'REMINDER_SENT', 'TIMEOUT_WARNING', 'AI_PROCESSING'
    )),
    event_data JSONB DEFAULT '{}'::jsonb,
    
    -- Event source
    triggered_by TEXT, -- User/system that triggered the event
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL, -- Related message if applicable
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for order_session_events
CREATE INDEX idx_session_events_session ON order_session_events(order_session_id);
CREATE INDEX idx_session_events_type ON order_session_events(event_type);
CREATE INDEX idx_session_events_created_at ON order_session_events(created_at DESC);

-- Add comments for order_session_events
COMMENT ON TABLE order_session_events IS 'Audit trail of all events within order collection sessions';
COMMENT ON COLUMN order_session_events.event_type IS 'Type of event that occurred in the session';
COMMENT ON COLUMN order_session_events.event_data IS 'Additional context data for the event';

-- =====================================================
-- PART 5: Add Row Level Security (RLS) policies
-- =====================================================

-- Enable RLS on new tables
ALTER TABLE conversation_order_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_session_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_session_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies for conversation_order_sessions
CREATE POLICY order_sessions_tenant_isolation ON conversation_order_sessions
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY order_sessions_insert_policy ON conversation_order_sessions
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

-- RLS Policies for order_session_items
CREATE POLICY session_items_tenant_isolation ON order_session_items
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM conversation_order_sessions s 
            WHERE s.id = order_session_items.order_session_id 
            AND (s.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY session_items_insert_policy ON order_session_items
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversation_order_sessions s 
            WHERE s.id = order_session_items.order_session_id 
            AND (s.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

-- RLS Policies for order_session_events
CREATE POLICY session_events_tenant_isolation ON order_session_events
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM conversation_order_sessions s 
            WHERE s.id = order_session_events.order_session_id 
            AND (s.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY session_events_insert_policy ON order_session_events
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversation_order_sessions s 
            WHERE s.id = order_session_events.order_session_id 
            AND (s.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

-- =====================================================
-- PART 6: Create helper functions
-- =====================================================

-- Function to get active session for a conversation
CREATE OR REPLACE FUNCTION get_active_order_session(conv_id UUID)
RETURNS UUID AS $$
DECLARE
    session_id UUID;
BEGIN
    SELECT id INTO session_id
    FROM conversation_order_sessions
    WHERE conversation_id = conv_id
      AND status IN ('ACTIVE', 'COLLECTING', 'REVIEWING')
    ORDER BY created_at DESC
    LIMIT 1;
    
    RETURN session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to automatically close timed-out sessions
CREATE OR REPLACE FUNCTION close_timed_out_sessions()
RETURNS INTEGER AS $$
DECLARE
    closed_count INTEGER;
BEGIN
    WITH closed_sessions AS (
        UPDATE conversation_order_sessions
        SET status = 'CLOSED',
            outcome = 'TIMEOUT',
            outcome_reason = 'Session closed due to inactivity',
            closed_at = NOW(),
            closed_by = 'SYSTEM',
            updated_at = NOW()
        WHERE status IN ('ACTIVE', 'COLLECTING')
          AND created_at < NOW() - (auto_close_timeout_minutes || ' minutes')::INTERVAL
          AND closed_at IS NULL
        RETURNING id
    )
    SELECT COUNT(*) INTO closed_count FROM closed_sessions;
    
    RETURN closed_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to consolidate session items into an order
CREATE OR REPLACE FUNCTION consolidate_order_session(session_id UUID)
RETURNS UUID AS $$
DECLARE
    new_order_id UUID;
    session_record RECORD;
    total_amount DECIMAL(10,2);
BEGIN
    -- Get session details
    SELECT * INTO session_record
    FROM conversation_order_sessions
    WHERE id = session_id AND status = 'REVIEWING';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Session not found or not in REVIEWING status';
    END IF;
    
    -- Calculate total amount from confirmed items
    SELECT COALESCE(SUM(quantity * unit_price), 0) INTO total_amount
    FROM order_session_items
    WHERE order_session_id = session_id AND status = 'CONFIRMED';
    
    -- Create consolidated order
    INSERT INTO orders (
        customer_id,
        conversation_id,
        distributor_id,
        channel,
        status,
        received_date,
        received_time,
        total_amount,
        ai_generated,
        order_session_id,
        is_consolidated
    )
    SELECT
        c.customer_id,
        c.id,
        c.distributor_id,
        c.channel,
        'CONFIRMED',
        CURRENT_DATE,
        CURRENT_TIME,
        total_amount,
        TRUE,
        session_id,
        TRUE
    FROM conversations c
    WHERE c.id = session_record.conversation_id
    RETURNING id INTO new_order_id;
    
    -- Copy confirmed items to order_products
    INSERT INTO order_products (
        order_id,
        product_id,
        product_name,
        product_code,
        quantity,
        unit_price,
        total_price
    )
    SELECT
        new_order_id,
        product_id,
        product_name,
        product_code,
        quantity,
        unit_price,
        quantity * unit_price
    FROM order_session_items
    WHERE order_session_id = session_id AND status = 'CONFIRMED';
    
    -- Update session with consolidated order reference
    UPDATE conversation_order_sessions
    SET consolidated_order_id = new_order_id,
        updated_at = NOW()
    WHERE id = session_id;
    
    RETURN new_order_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- PART 7: Create triggers
-- =====================================================

-- Trigger to log session status changes
CREATE OR REPLACE FUNCTION log_session_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO order_session_events (
            order_session_id,
            event_type,
            event_data,
            triggered_by
        ) VALUES (
            NEW.id,
            'STATUS_CHANGED',
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'timestamp', NOW()
            ),
            COALESCE(NEW.closed_by, NEW.created_by, 'SYSTEM')
        );
        
        -- Update status change timestamps
        CASE NEW.status
            WHEN 'COLLECTING' THEN
                NEW.collecting_started_at := NOW();
            WHEN 'REVIEWING' THEN
                NEW.review_started_at := NOW();
            WHEN 'CLOSED' THEN
                NEW.closed_at := NOW();
            ELSE
                -- No specific timestamp update
        END CASE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_session_status_change
    BEFORE UPDATE ON conversation_order_sessions
    FOR EACH ROW
    EXECUTE FUNCTION log_session_status_change();

-- Trigger to update conversation_order_sessions updated_at
CREATE TRIGGER update_conversation_order_sessions_updated_at
    BEFORE UPDATE ON conversation_order_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- PART 8: Grant permissions
-- =====================================================

-- Grant permissions to distributor_user role
GRANT SELECT, INSERT, UPDATE ON conversation_order_sessions TO distributor_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON order_session_items TO distributor_user;
GRANT SELECT, INSERT ON order_session_events TO distributor_user;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION get_active_order_session TO distributor_user;
GRANT EXECUTE ON FUNCTION consolidate_order_session TO distributor_user;

-- Grant permissions to platform_admin role
GRANT ALL ON conversation_order_sessions TO platform_admin;
GRANT ALL ON order_session_items TO platform_admin;
GRANT ALL ON order_session_events TO platform_admin;

-- =====================================================
-- PART 9: Create views for session analytics
-- =====================================================

-- View for active sessions summary
CREATE VIEW active_order_sessions_summary AS
SELECT 
    s.id as session_id,
    s.conversation_id,
    s.distributor_id,
    s.status,
    s.started_at,
    s.collecting_started_at,
    s.review_started_at,
    COUNT(DISTINCT i.id) as total_items,
    COUNT(DISTINCT CASE WHEN i.status = 'CONFIRMED' THEN i.id END) as confirmed_items,
    COALESCE(SUM(CASE WHEN i.status = 'CONFIRMED' THEN i.quantity * i.unit_price END), 0) as total_value,
    s.ai_confidence_avg,
    s.ai_interactions_count,
    EXTRACT(EPOCH FROM (NOW() - s.started_at))/60 as session_duration_minutes
FROM conversation_order_sessions s
LEFT JOIN order_session_items i ON i.order_session_id = s.id
WHERE s.status IN ('ACTIVE', 'COLLECTING', 'REVIEWING')
GROUP BY s.id;

-- Grant access to the views
GRANT SELECT ON active_order_sessions_summary TO distributor_user;
GRANT ALL ON active_order_sessions_summary TO platform_admin;

COMMENT ON VIEW active_order_sessions_summary IS 'Real-time summary of active order collection sessions';

-- =====================================================
-- PART 10: Add helpful comments and documentation
-- =====================================================

-- Add function comments
COMMENT ON FUNCTION get_active_order_session IS 'Returns the active order session ID for a given conversation';
COMMENT ON FUNCTION close_timed_out_sessions IS 'Automatically closes sessions that have exceeded their timeout period';
COMMENT ON FUNCTION consolidate_order_session IS 'Consolidates session items into a final order and returns the order ID';

-- Add trigger comments
COMMENT ON TRIGGER trigger_log_session_status_change ON conversation_order_sessions IS 'Logs all status changes to the session events table';

-- Final migration comment
COMMENT ON SCHEMA public IS 'Order Agent database schema with conversation order session management';