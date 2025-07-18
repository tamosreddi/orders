-- Enhance product catalog integration for AI order processing
-- Connects products to order_products and adds advanced product matching capabilities
-- Essential for AI agents to match customer messages to actual products

-- Add product matching fields to order_products table
ALTER TABLE order_products ADD COLUMN matched_product_id UUID REFERENCES products(id);
ALTER TABLE order_products ADD COLUMN matching_confidence DECIMAL(3,2) CHECK (matching_confidence >= 0 AND matching_confidence <= 1);
ALTER TABLE order_products ADD COLUMN matching_method TEXT CHECK (matching_method IN ('EXACT_MATCH', 'FUZZY_MATCH', 'AI_MATCH', 'MANUAL_OVERRIDE'));
ALTER TABLE order_products ADD COLUMN matching_score DECIMAL(5,4); -- Detailed matching score for analytics
ALTER TABLE order_products ADD COLUMN alternative_matches JSONB DEFAULT '[]'::jsonb; -- Other potential matches

-- Enhance products table for better AI matching
ALTER TABLE products ADD COLUMN brand TEXT;
ALTER TABLE products ADD COLUMN model TEXT;
ALTER TABLE products ADD COLUMN size_variants JSONB DEFAULT '[]'::jsonb; -- Different sizes/weights available
ALTER TABLE products ADD COLUMN seasonal BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN minimum_order_quantity INTEGER DEFAULT 1;
ALTER TABLE products ADD COLUMN maximum_order_quantity INTEGER;
ALTER TABLE products ADD COLUMN lead_time_days INTEGER DEFAULT 0;

-- AI matching enhancement fields
ALTER TABLE products ADD COLUMN ai_training_examples JSONB DEFAULT '[]'::jsonb; -- Example phrases customers use
ALTER TABLE products ADD COLUMN common_misspellings JSONB DEFAULT '[]'::jsonb; -- Common misspellings
ALTER TABLE products ADD COLUMN seasonal_patterns JSONB DEFAULT '[]'::jsonb; -- When product is typically ordered

-- Product categorization enhancement
CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    parent_category_id UUID REFERENCES product_categories(id),
    description TEXT,
    ai_keywords JSONB DEFAULT '[]'::jsonb, -- Keywords for AI classification
    sort_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, name, parent_category_id)
);

-- Add category reference to products
ALTER TABLE products ADD COLUMN category_id UUID REFERENCES product_categories(id);

-- Product variants table (sizes, colors, etc.)
CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Variant details
    variant_name TEXT NOT NULL, -- "Small", "Large", "Red", "500ml", etc.
    variant_type TEXT NOT NULL, -- "SIZE", "COLOR", "VOLUME", "WEIGHT", etc.
    sku TEXT, -- Unique SKU for this variant
    
    -- Pricing for this variant
    unit_price DECIMAL(10,2),
    price_difference DECIMAL(10,2) DEFAULT 0, -- Difference from base product price
    
    -- Inventory for this variant
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 5,
    
    -- AI matching for variants
    ai_aliases JSONB DEFAULT '[]'::jsonb, -- "small", "sm", "S", "little"
    sort_order INTEGER DEFAULT 0,
    
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(product_id, variant_name, variant_type)
);

-- Product bundle/combo table
CREATE TABLE product_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Bundle details
    bundle_name TEXT NOT NULL,
    description TEXT,
    bundle_sku TEXT,
    
    -- Pricing
    bundle_price DECIMAL(10,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- AI matching
    ai_keywords JSONB DEFAULT '[]'::jsonb,
    common_names JSONB DEFAULT '[]'::jsonb, -- "combo", "package", "deal"
    
    -- Availability
    active BOOLEAN DEFAULT TRUE,
    seasonal BOOLEAN DEFAULT FALSE,
    available_from DATE,
    available_until DATE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bundle items (what products are in each bundle)
CREATE TABLE product_bundle_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_id UUID NOT NULL REFERENCES product_bundles(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id UUID REFERENCES product_variants(id), -- Optional specific variant
    quantity INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    
    -- Ensure unique combination of bundle, product, and variant
    UNIQUE(bundle_id, product_id, variant_id)
);

-- Product matching history (for AI improvement)
CREATE TABLE product_matching_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_product_id UUID NOT NULL REFERENCES order_products(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Original text from customer
    original_text TEXT NOT NULL,
    
    -- AI suggestions
    ai_suggestions JSONB DEFAULT '[]'::jsonb, -- Array of suggested products with scores
    
    -- Final result
    final_product_id UUID REFERENCES products(id),
    final_variant_id UUID REFERENCES product_variants(id),
    was_manual_override BOOLEAN DEFAULT FALSE,
    
    -- Feedback
    accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    feedback_notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_order_products_matched_product ON order_products(matched_product_id);
CREATE INDEX IF NOT EXISTS idx_order_products_matching_confidence ON order_products(matching_confidence DESC);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_seasonal ON products(seasonal);

CREATE INDEX IF NOT EXISTS idx_product_categories_distributor ON product_categories(distributor_id);
CREATE INDEX IF NOT EXISTS idx_product_categories_parent ON product_categories(parent_category_id);

CREATE INDEX IF NOT EXISTS idx_product_variants_product ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_distributor ON product_variants(distributor_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_type ON product_variants(variant_type);

CREATE INDEX IF NOT EXISTS idx_product_bundles_distributor ON product_bundles(distributor_id);
CREATE INDEX IF NOT EXISTS idx_product_bundles_active ON product_bundles(active) WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS idx_product_matching_history_distributor ON product_matching_history(distributor_id);
CREATE INDEX IF NOT EXISTS idx_product_matching_history_created_at ON product_matching_history(created_at DESC);

-- GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_products_aliases_gin ON products USING GIN (aliases);
CREATE INDEX IF NOT EXISTS idx_products_keywords_gin ON products USING GIN (keywords);
CREATE INDEX IF NOT EXISTS idx_products_ai_training_gin ON products USING GIN (ai_training_examples);
CREATE INDEX IF NOT EXISTS idx_product_categories_keywords_gin ON product_categories USING GIN (ai_keywords);
CREATE INDEX IF NOT EXISTS idx_product_variants_aliases_gin ON product_variants USING GIN (ai_aliases);
CREATE INDEX IF NOT EXISTS idx_product_bundles_keywords_gin ON product_bundles USING GIN (ai_keywords);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_products_search ON products USING gin(to_tsvector('english', 
    name || ' ' || COALESCE(description, '') || ' ' || COALESCE(brand, '') || ' ' || COALESCE(model, '')
));

-- Function to calculate product matching score
CREATE OR REPLACE FUNCTION calculate_product_match_score(
    search_text TEXT,
    product_record products,
    variant_record product_variants DEFAULT NULL
)
RETURNS DECIMAL(5,4) AS $$
DECLARE
    score DECIMAL(5,4) := 0;
    normalized_search TEXT;
    product_tokens TEXT[];
    search_tokens TEXT[];
    common_tokens INTEGER := 0;
    total_tokens INTEGER;
BEGIN
    -- Normalize search text
    normalized_search := LOWER(TRIM(search_text));
    
    -- Exact name match gets highest score
    IF LOWER(product_record.name) = normalized_search THEN
        RETURN 1.0000;
    END IF;
    
    -- Check aliases for exact match
    IF product_record.aliases ? normalized_search THEN
        RETURN 0.9500;
    END IF;
    
    -- Tokenize for partial matching
    search_tokens := string_to_array(normalized_search, ' ');
    product_tokens := string_to_array(
        LOWER(product_record.name || ' ' || COALESCE(product_record.description, '') || ' ' || 
              COALESCE(product_record.brand, '') || ' ' || COALESCE(product_record.model, '')), 
        ' '
    );
    
    -- Count common tokens
    SELECT COUNT(*)
    INTO common_tokens
    FROM unnest(search_tokens) AS search_token
    WHERE search_token = ANY(product_tokens) AND LENGTH(search_token) > 2;
    
    total_tokens := array_length(search_tokens, 1);
    
    -- Calculate base score from token matching
    IF total_tokens > 0 THEN
        score := (common_tokens::DECIMAL / total_tokens) * 0.8;
    END IF;
    
    -- Bonus for brand match
    IF product_record.brand IS NOT NULL AND position(LOWER(product_record.brand) in normalized_search) > 0 THEN
        score := score + 0.1;
    END IF;
    
    -- Bonus for category keywords match
    -- (This would require joining with category data)
    
    -- Apply variant bonus if specified
    IF variant_record IS NOT NULL THEN
        IF variant_record.ai_aliases ? ANY(search_tokens) THEN
            score := score + 0.05;
        END IF;
    END IF;
    
    RETURN LEAST(score, 1.0000);
END;
$$ LANGUAGE plpgsql;

-- Function to find product matches for AI
CREATE OR REPLACE FUNCTION find_product_matches(
    search_text TEXT,
    dist_id UUID,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.3,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    product_id UUID,
    variant_id UUID,
    product_name TEXT,
    variant_name TEXT,
    match_score DECIMAL(5,4),
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH product_scores AS (
        SELECT 
            p.id as product_id,
            NULL::UUID as variant_id,
            p.name as product_name,
            NULL::TEXT as variant_name,
            calculate_product_match_score(search_text, p) as match_score,
            'PRODUCT' as match_type
        FROM products p
        WHERE p.distributor_id = dist_id 
        AND p.active = TRUE
        
        UNION ALL
        
        SELECT 
            p.id as product_id,
            pv.id as variant_id,
            p.name as product_name,
            pv.variant_name as variant_name,
            calculate_product_match_score(search_text, p, pv) as match_score,
            'VARIANT' as match_type
        FROM products p
        JOIN product_variants pv ON pv.product_id = p.id
        WHERE p.distributor_id = dist_id 
        AND p.active = TRUE 
        AND pv.active = TRUE
    )
    SELECT *
    FROM product_scores
    WHERE match_score >= confidence_threshold
    ORDER BY match_score DESC, product_name ASC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to update product from order feedback
CREATE OR REPLACE FUNCTION update_product_from_feedback(
    product_match_history_id UUID,
    correct_product_id UUID,
    correct_variant_id UUID DEFAULT NULL,
    rating INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    history_record product_matching_history%ROWTYPE;
    search_text TEXT;
BEGIN
    -- Get the history record
    SELECT * INTO history_record FROM product_matching_history WHERE id = product_match_history_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product matching history record not found';
    END IF;
    
    search_text := history_record.original_text;
    
    -- Update the history record
    UPDATE product_matching_history 
    SET 
        final_product_id = correct_product_id,
        final_variant_id = correct_variant_id,
        accuracy_rating = rating,
        was_manual_override = TRUE
    WHERE id = product_match_history_id;
    
    -- Add the search text to the product's training examples if rating is good
    IF rating >= 4 AND correct_product_id IS NOT NULL THEN
        UPDATE products 
        SET ai_training_examples = ai_training_examples || jsonb_build_array(search_text)
        WHERE id = correct_product_id
        AND NOT ai_training_examples ? search_text;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically create matching history
CREATE OR REPLACE FUNCTION create_product_matching_history()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create history for AI-extracted products with original text
    IF NEW.ai_extracted = TRUE AND NEW.ai_original_text IS NOT NULL THEN
        INSERT INTO product_matching_history (
            order_product_id,
            distributor_id,
            original_text,
            final_product_id,
            final_variant_id,
            was_manual_override
        ) VALUES (
            NEW.id,
            (SELECT distributor_id FROM orders WHERE id = NEW.order_id),
            NEW.ai_original_text,
            NEW.matched_product_id,
            NULL, -- TODO: Add variant support to order_products if needed
            NEW.manual_override
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_product_matching_history
    AFTER INSERT ON order_products
    FOR EACH ROW EXECUTE FUNCTION create_product_matching_history();

-- Add updated_at triggers for new tables
CREATE TRIGGER trigger_product_categories_updated_at
    BEFORE UPDATE ON product_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_product_variants_updated_at
    BEFORE UPDATE ON product_variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_product_bundles_updated_at
    BEFORE UPDATE ON product_bundles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS policies for new tables
ALTER TABLE product_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_bundles ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_bundle_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_matching_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY product_categories_tenant_isolation ON product_categories
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY product_variants_tenant_isolation ON product_variants
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY product_bundles_tenant_isolation ON product_bundles
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY product_bundle_items_tenant_isolation ON product_bundle_items
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM product_bundles pb 
            WHERE pb.id = product_bundle_items.bundle_id 
            AND (pb.distributor_id = get_current_distributor_id() OR is_service_role())
        )
    );

CREATE POLICY product_matching_history_tenant_isolation ON product_matching_history
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

-- Grant permissions to distributor_user role
GRANT SELECT, INSERT, UPDATE ON product_categories TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON product_variants TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON product_bundles TO distributor_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON product_bundle_items TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON product_matching_history TO distributor_user;
GRANT EXECUTE ON FUNCTION find_product_matches TO distributor_user;
GRANT EXECUTE ON FUNCTION update_product_from_feedback TO distributor_user;

-- Insert some example product categories for testing
INSERT INTO product_categories (distributor_id, name, ai_keywords) 
SELECT 
    d.id,
    category_name,
    keywords::jsonb
FROM distributors d,
(VALUES 
    ('Dairy Products', '["milk", "cheese", "yogurt", "butter", "cream", "dairy"]'),
    ('Meat & Poultry', '["meat", "beef", "chicken", "pork", "lamb", "poultry", "carnes"]'),
    ('Beverages', '["drink", "beverage", "soda", "juice", "water", "beer", "wine"]'),
    ('Frozen Foods', '["frozen", "ice cream", "frozen vegetables", "frozen meals"]'),
    ('Bakery', '["bread", "cake", "pastry", "bakery", "baked goods"]'),
    ('Fresh Produce', '["fruits", "vegetables", "fresh", "produce", "organic"]')
) AS categories(category_name, keywords);

-- Add comments for documentation
COMMENT ON TABLE product_categories IS 'Hierarchical product categorization with AI keyword support';
COMMENT ON TABLE product_variants IS 'Product variants (sizes, colors, etc.) with AI matching';
COMMENT ON TABLE product_bundles IS 'Product bundles and combo packages';
COMMENT ON TABLE product_matching_history IS 'History of AI product matching for learning and improvement';

COMMENT ON FUNCTION calculate_product_match_score IS 'Calculates similarity score between search text and product';
COMMENT ON FUNCTION find_product_matches IS 'Finds matching products for AI order processing';
COMMENT ON FUNCTION update_product_from_feedback IS 'Updates product AI training data based on user feedback';