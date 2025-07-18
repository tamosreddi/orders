-- Create orders table
-- Enhanced version of existing Order/OrderDetails interfaces
-- Integrates with messages for AI-generated orders

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL, -- Optional: if order came from conversation
    
    -- Channel and status (from existing Order interface)
    channel TEXT NOT NULL CHECK (channel IN ('WHATSAPP', 'SMS', 'EMAIL')), -- Order.channel
    status TEXT NOT NULL CHECK (status IN ('CONFIRMED', 'PENDING', 'REVIEW')) DEFAULT 'PENDING', -- Order.status
    
    -- Date and time fields (from OrderDetails interface)
    received_date DATE NOT NULL, -- OrderDetails.receivedDate
    received_time TIME NOT NULL, -- OrderDetails.receivedTime
    delivery_date DATE, -- OrderDetails.deliveryDate
    
    -- Location information
    postal_code TEXT, -- OrderDetails.postalCode
    delivery_address TEXT, -- OrderDetails.customer.address (can override customer default)
    
    -- Financial information
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0, -- OrderDetails.totalAmount
    
    -- Additional information
    additional_comment TEXT, -- OrderDetails.additionalComment
    whatsapp_message TEXT, -- OrderDetails.whatsappMessage (original message)
    
    -- AI processing metadata
    ai_generated BOOLEAN DEFAULT FALSE, -- Whether this order was created by AI
    ai_confidence DECIMAL(3,2), -- AI confidence in order extraction (0.00 to 1.00)
    ai_source_message_id UUID REFERENCES messages(id), -- Source message if AI-generated
    
    -- Order processing workflow
    requires_review BOOLEAN DEFAULT FALSE, -- Whether order needs manual review
    reviewed_by TEXT, -- User who reviewed the order
    reviewed_at TIMESTAMPTZ, -- When order was reviewed
    
    -- External references
    external_order_id TEXT, -- Reference to external systems
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create order attachments table (from OrderDetails.attachments)
CREATE TABLE order_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL, -- URL to stored file
    file_name TEXT NOT NULL, -- Original filename
    file_type TEXT, -- MIME type
    file_size INTEGER, -- Size in bytes
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_channel ON orders(channel);
CREATE INDEX idx_orders_received_date ON orders(received_date DESC);
CREATE INDEX idx_orders_delivery_date ON orders(delivery_date);
CREATE INDEX idx_orders_ai_generated ON orders(ai_generated);
CREATE INDEX idx_orders_conversation ON orders(conversation_id) WHERE conversation_id IS NOT NULL;
CREATE INDEX idx_orders_requires_review ON orders(requires_review) WHERE requires_review = TRUE;

-- Indexes for order attachments
CREATE INDEX idx_order_attachments_order ON order_attachments(order_id);

-- Add comments for documentation
COMMENT ON TABLE orders IS 'Orders table supporting Order and OrderDetails TypeScript interfaces';
COMMENT ON COLUMN orders.channel IS 'Order source channel (Order.channel): WHATSAPP, SMS, EMAIL';
COMMENT ON COLUMN orders.status IS 'Order status (Order.status): CONFIRMED, PENDING, REVIEW';
COMMENT ON COLUMN orders.received_date IS 'Date order was received (OrderDetails.receivedDate)';
COMMENT ON COLUMN orders.received_time IS 'Time order was received (OrderDetails.receivedTime)';
COMMENT ON COLUMN orders.delivery_date IS 'Requested delivery date (OrderDetails.deliveryDate)';
COMMENT ON COLUMN orders.total_amount IS 'Total order amount (OrderDetails.totalAmount)';
COMMENT ON COLUMN orders.ai_generated IS 'True if order was created by AI from message processing';
COMMENT ON COLUMN orders.ai_confidence IS 'AI confidence score for automatically generated orders';
COMMENT ON COLUMN orders.requires_review IS 'Whether order needs manual review before confirmation';

COMMENT ON TABLE order_attachments IS 'File attachments for orders (OrderDetails.attachments)';