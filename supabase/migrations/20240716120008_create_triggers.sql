-- Create triggers for data consistency and real-time updates
-- These triggers maintain data integrity and update aggregated fields automatically

-- Function to update customer statistics when orders change
CREATE OR REPLACE FUNCTION update_customer_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle INSERT and UPDATE
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE customers SET
            total_orders = (
                SELECT COUNT(*) 
                FROM orders 
                WHERE customer_id = NEW.customer_id
            ),
            total_spent = (
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM orders 
                WHERE customer_id = NEW.customer_id AND status = 'CONFIRMED'
            ),
            last_ordered_date = (
                SELECT MAX(received_date) 
                FROM orders 
                WHERE customer_id = NEW.customer_id
            ),
            updated_at = NOW()
        WHERE id = NEW.customer_id;
        
        -- Update customer status based on order activity
        UPDATE customers SET
            status = CASE
                WHEN last_ordered_date IS NULL THEN 'NO_ORDERS_YET'
                WHEN last_ordered_date > NOW() - INTERVAL '30 days' THEN 'ORDERING'
                WHEN last_ordered_date > NOW() - INTERVAL '90 days' THEN 'AT_RISK'
                ELSE 'STOPPED_ORDERING'
            END
        WHERE id = NEW.customer_id;
        
        RETURN NEW;
    END IF;
    
    -- Handle DELETE
    IF TG_OP = 'DELETE' THEN
        UPDATE customers SET
            total_orders = (
                SELECT COUNT(*) 
                FROM orders 
                WHERE customer_id = OLD.customer_id
            ),
            total_spent = (
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM orders 
                WHERE customer_id = OLD.customer_id AND status = 'CONFIRMED'
            ),
            last_ordered_date = (
                SELECT MAX(received_date) 
                FROM orders 
                WHERE customer_id = OLD.customer_id
            ),
            updated_at = NOW()
        WHERE id = OLD.customer_id;
        
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for customer stats updates
CREATE TRIGGER trigger_update_customer_stats
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_customer_stats();

-- Function to update conversation metadata when messages change
CREATE OR REPLACE FUNCTION update_conversation_metadata()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle INSERT and UPDATE
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE conversations SET
            last_message_at = NEW.created_at,
            unread_count = CASE
                WHEN NEW.is_from_customer THEN unread_count + 1
                ELSE unread_count
            END,
            updated_at = NOW()
        WHERE id = NEW.conversation_id;
        
        RETURN NEW;
    END IF;
    
    -- Handle DELETE
    IF TG_OP = 'DELETE' THEN
        UPDATE conversations SET
            last_message_at = (
                SELECT MAX(created_at) 
                FROM messages 
                WHERE conversation_id = OLD.conversation_id
            ),
            unread_count = (
                SELECT COUNT(*) 
                FROM messages 
                WHERE conversation_id = OLD.conversation_id 
                AND is_from_customer = TRUE 
                AND status != 'READ'
            ),
            updated_at = NOW()
        WHERE id = OLD.conversation_id;
        
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for conversation metadata updates
CREATE TRIGGER trigger_update_conversation_metadata
    AFTER INSERT OR UPDATE OR DELETE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_metadata();

-- Function to calculate order total when order products change
CREATE OR REPLACE FUNCTION update_order_total()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle INSERT, UPDATE, DELETE for order products
    IF TG_OP = 'DELETE' THEN
        UPDATE orders SET
            total_amount = (
                SELECT COALESCE(SUM(line_price), 0) 
                FROM order_products 
                WHERE order_id = OLD.order_id
            ),
            updated_at = NOW()
        WHERE id = OLD.order_id;
        
        RETURN OLD;
    ELSE
        UPDATE orders SET
            total_amount = (
                SELECT COALESCE(SUM(line_price), 0) 
                FROM order_products 
                WHERE order_id = NEW.order_id
            ),
            updated_at = NOW()
        WHERE id = NEW.order_id;
        
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger for order total updates
CREATE TRIGGER trigger_update_order_total
    AFTER INSERT OR UPDATE OR DELETE ON order_products
    FOR EACH ROW EXECUTE FUNCTION update_order_total();

-- Function to update message template usage statistics
CREATE OR REPLACE FUNCTION update_template_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- This would be called when a template is used in AI responses
    -- For now, it's a placeholder for future implementation
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to mark messages as read when status changes
CREATE OR REPLACE FUNCTION update_message_read_status()
RETURNS TRIGGER AS $$
BEGIN
    -- When message status changes to 'read', update conversation unread count
    IF NEW.status = 'read' AND OLD.status != 'read' AND NEW.is_from_customer = TRUE THEN
        UPDATE conversations SET
            unread_count = GREATEST(0, unread_count - 1),
            updated_at = NOW()
        WHERE id = NEW.conversation_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for message read status updates
CREATE TRIGGER trigger_update_message_read_status
    AFTER UPDATE OF status ON messages
    FOR EACH ROW EXECUTE FUNCTION update_message_read_status();

-- Function to automatically set requires_review for AI-generated orders
CREATE OR REPLACE FUNCTION set_order_review_requirement()
RETURNS TRIGGER AS $$
BEGIN
    -- If order is AI-generated with low confidence, require review
    IF NEW.ai_generated = TRUE AND (NEW.ai_confidence IS NULL OR NEW.ai_confidence < 0.8) THEN
        NEW.requires_review = TRUE;
    END IF;
    
    -- If order total is above threshold, require review
    IF NEW.total_amount > 1000.00 THEN
        NEW.requires_review = TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for order review requirements
CREATE TRIGGER trigger_set_order_review_requirement
    BEFORE INSERT OR UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION set_order_review_requirement();

-- Function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER trigger_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_order_products_updated_at
    BEFORE UPDATE ON order_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_message_templates_updated_at
    BEFORE UPDATE ON message_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON FUNCTION update_customer_stats IS 'Updates customer aggregated statistics when orders change';
COMMENT ON FUNCTION update_conversation_metadata IS 'Updates conversation last message time and unread count';
COMMENT ON FUNCTION update_order_total IS 'Recalculates order total when order products change';
COMMENT ON FUNCTION update_message_read_status IS 'Updates conversation unread count when messages are marked as read';
COMMENT ON FUNCTION set_order_review_requirement IS 'Automatically sets review requirement for AI orders and high-value orders';
COMMENT ON FUNCTION update_updated_at_column IS 'Automatically updates updated_at timestamp on record changes';