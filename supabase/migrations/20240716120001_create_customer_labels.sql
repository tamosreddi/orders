-- Create customer labels system
-- Supports the CustomerLabel interface and many-to-many relationship
-- Allows customers to have multiple labels (Dairy, Carnes, Restaurant, Bar, etc.)

-- Labels definition table
CREATE TABLE customer_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE, -- CustomerLabel.name
    color TEXT NOT NULL,        -- CustomerLabel.color (hex color code)
    description TEXT,           -- Optional description for the label
    is_predefined BOOLEAN DEFAULT FALSE, -- Whether this is a system predefined label
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many relationship between customers and labels
CREATE TABLE customer_label_assignments (
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    label_id UUID REFERENCES customer_labels(id) ON DELETE CASCADE,
    value TEXT, -- CustomerLabel.value (optional additional value)
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (customer_id, label_id)
);

-- Insert predefined labels from TypeScript interface
INSERT INTO customer_labels (name, color, is_predefined) VALUES
('Dairy', '#FEF3C7', true),
('Carnes', '#FEE2E2', true),
('Restaurant', '#E0F2FE', true),
('Bar', '#F3E8FF', true);

-- Create indexes for performance
CREATE INDEX idx_customer_labels_name ON customer_labels(name);
CREATE INDEX idx_customer_label_assignments_customer ON customer_label_assignments(customer_id);
CREATE INDEX idx_customer_label_assignments_label ON customer_label_assignments(label_id);

-- Add comments for documentation
COMMENT ON TABLE customer_labels IS 'Label definitions supporting CustomerLabel TypeScript interface';
COMMENT ON TABLE customer_label_assignments IS 'Many-to-many relationship between customers and labels';
COMMENT ON COLUMN customer_labels.name IS 'Label name (CustomerLabel.name)';
COMMENT ON COLUMN customer_labels.color IS 'Hex color code for UI display (CustomerLabel.color)';
COMMENT ON COLUMN customer_label_assignments.value IS 'Optional label value (CustomerLabel.value)';