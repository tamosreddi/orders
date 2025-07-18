-- Create customers table
-- This is the foundation table that stores all customer/business information
-- Supports both the existing Customer interface and future message integration

CREATE TABLE customers (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Business information (maps to Customer interface)
    business_name TEXT NOT NULL, -- Customer.name
    contact_person_name TEXT,    -- Customer.customerName (optional person responsible)
    customer_code TEXT UNIQUE NOT NULL, -- Customer.code (unique identifier)
    
    -- Contact information
    email TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    avatar_url TEXT, -- Customer.avatar
    
    -- Status fields (existing Customer interface)
    status TEXT CHECK (status IN ('ORDERING', 'AT_RISK', 'STOPPED_ORDERING', 'NO_ORDERS_YET')) DEFAULT 'NO_ORDERS_YET',
    invitation_status TEXT CHECK (invitation_status IN ('ACTIVE', 'PENDING')) DEFAULT 'PENDING',
    
    -- Important dates
    joined_date TIMESTAMPTZ DEFAULT NOW(),
    last_ordered_date TIMESTAMPTZ, -- Customer.lastOrdered
    expected_order_date TIMESTAMPTZ, -- Customer.expectedOrder
    
    -- Aggregated statistics (updated via triggers)
    total_orders INTEGER DEFAULT 0, -- Customer.totalOrders
    total_spent DECIMAL(10,2) DEFAULT 0, -- Customer.totalSpent
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create basic indexes for performance
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_status ON customers(status, invitation_status);
CREATE INDEX idx_customers_last_ordered ON customers(last_ordered_date);

-- Add comments for documentation
COMMENT ON TABLE customers IS 'Core customer/business information supporting both existing Customer interface and future message integration';
COMMENT ON COLUMN customers.business_name IS 'Business name (Customer.name in TypeScript interface)';
COMMENT ON COLUMN customers.contact_person_name IS 'Person responsible for business (Customer.customerName)';
COMMENT ON COLUMN customers.customer_code IS 'Unique customer identifier (Customer.code)';
COMMENT ON COLUMN customers.status IS 'Customer ordering status for business logic';
COMMENT ON COLUMN customers.invitation_status IS 'Platform invitation status (ACTIVE/PENDING)';