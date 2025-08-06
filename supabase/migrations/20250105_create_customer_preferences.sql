-- Create customer_preferences table for autonomous agent learning
CREATE TABLE IF NOT EXISTS public.customer_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id UUID NOT NULL REFERENCES public.customers(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES public.distributors(id) ON DELETE CASCADE,
    preference_type TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    learned_from TEXT NOT NULL, -- conversation_id, order_id, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    
    -- Ensure unique preference per customer/distributor/type
    UNIQUE(customer_id, distributor_id, preference_type)
);

-- Create indexes for performance
CREATE INDEX idx_customer_preferences_customer_id ON public.customer_preferences(customer_id);
CREATE INDEX idx_customer_preferences_distributor_id ON public.customer_preferences(distributor_id);
CREATE INDEX idx_customer_preferences_type ON public.customer_preferences(preference_type);
CREATE INDEX idx_customer_preferences_created_at ON public.customer_preferences(created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_customer_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
CREATE TRIGGER customer_preferences_updated_at_trigger
    BEFORE UPDATE ON public.customer_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_preferences_updated_at();

-- Add RLS policies
ALTER TABLE public.customer_preferences ENABLE ROW LEVEL SECURITY;

-- Policy for distributors to manage their own customer preferences
CREATE POLICY "Distributors can manage their customer preferences"
    ON public.customer_preferences
    FOR ALL
    USING (distributor_id = auth.uid())
    WITH CHECK (distributor_id = auth.uid());

-- Grant necessary permissions
GRANT ALL ON public.customer_preferences TO authenticated;
GRANT ALL ON public.customer_preferences TO service_role;

-- Add comment for documentation
COMMENT ON TABLE public.customer_preferences IS 'Stores learned customer preferences for the autonomous AI agent';
COMMENT ON COLUMN public.customer_preferences.preference_type IS 'Type of preference (e.g., product_preference, order_frequency, preferred_brands)';
COMMENT ON COLUMN public.customer_preferences.value IS 'The preference value or description';
COMMENT ON COLUMN public.customer_preferences.confidence IS 'AI confidence in this preference (0.0 to 1.0)';
COMMENT ON COLUMN public.customer_preferences.learned_from IS 'Source of this preference learning (conversation_id, order_id, etc.)';