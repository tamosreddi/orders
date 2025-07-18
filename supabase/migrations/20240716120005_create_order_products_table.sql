-- Create order products table
-- Line items for orders, supporting OrderProduct interface
-- Each order can have multiple products with quantities and pricing

CREATE TABLE order_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Product information (from OrderProduct interface)
    product_name TEXT NOT NULL, -- OrderProduct.name (for now, text-based. Future: product_id reference)
    product_unit TEXT NOT NULL, -- OrderProduct.unit (kg, units, boxes, etc.)
    
    -- Quantity and pricing
    quantity INTEGER NOT NULL CHECK (quantity > 0), -- OrderProduct.quantity
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0), -- OrderProduct.unitPrice
    line_price DECIMAL(10,2) NOT NULL CHECK (line_price >= 0), -- OrderProduct.linePrice
    
    -- AI extraction metadata
    ai_extracted BOOLEAN DEFAULT FALSE, -- Whether this line item was extracted by AI
    ai_confidence DECIMAL(3,2), -- AI confidence in product identification
    ai_original_text TEXT, -- Original text from message that AI interpreted
    
    -- Product matching (for future catalog integration)
    suggested_product_id UUID, -- Future reference to products table
    manual_override BOOLEAN DEFAULT FALSE, -- Whether user manually corrected AI extraction
    
    -- Line item metadata
    line_order INTEGER DEFAULT 1, -- Order of items in the product list
    notes TEXT, -- Additional notes for this line item
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_order_products_order ON order_products(order_id);
CREATE INDEX idx_order_products_name ON order_products(product_name);
CREATE INDEX idx_order_products_ai_extracted ON order_products(ai_extracted);
CREATE INDEX idx_order_products_line_order ON order_products(order_id, line_order);

-- Add constraint to ensure line_price matches quantity * unit_price (with tolerance for rounding)
CREATE OR REPLACE FUNCTION check_line_price()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow small rounding differences (within 0.01)
    IF ABS(NEW.line_price - (NEW.quantity * NEW.unit_price)) > 0.01 THEN
        RAISE EXCEPTION 'line_price (%) must equal quantity (%) * unit_price (%)', 
            NEW.line_price, NEW.quantity, NEW.unit_price;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_line_price
    BEFORE INSERT OR UPDATE ON order_products
    FOR EACH ROW EXECUTE FUNCTION check_line_price();

-- Add comments for documentation
COMMENT ON TABLE order_products IS 'Order line items supporting OrderProduct TypeScript interface';
COMMENT ON COLUMN order_products.product_name IS 'Product name (OrderProduct.name)';
COMMENT ON COLUMN order_products.product_unit IS 'Unit of measurement (OrderProduct.unit): kg, units, boxes, etc.';
COMMENT ON COLUMN order_products.quantity IS 'Quantity ordered (OrderProduct.quantity)';
COMMENT ON COLUMN order_products.unit_price IS 'Price per unit (OrderProduct.unitPrice)';
COMMENT ON COLUMN order_products.line_price IS 'Total line price (OrderProduct.linePrice)';
COMMENT ON COLUMN order_products.ai_extracted IS 'True if line item was extracted by AI from message';
COMMENT ON COLUMN order_products.ai_original_text IS 'Original message text that AI interpreted as this product';
COMMENT ON COLUMN order_products.line_order IS 'Display order of products in the order';
COMMENT ON FUNCTION check_line_price IS 'Ensures line_price equals quantity * unit_price';