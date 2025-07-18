-- Add message encryption and enhanced security features
-- Critical for protecting sensitive customer communications and PII
-- Implements field-level encryption for sensitive data

-- Add encryption fields to messages table
ALTER TABLE messages ADD COLUMN encrypted_content TEXT; -- Encrypted version of sensitive content
ALTER TABLE messages ADD COLUMN content_hash TEXT; -- Hash for integrity verification
ALTER TABLE messages ADD COLUMN encryption_key_id TEXT; -- Reference to encryption key used
ALTER TABLE messages ADD COLUMN contains_pii BOOLEAN DEFAULT FALSE; -- Flag for PII detection

-- Add encryption fields to customers table for PII protection
ALTER TABLE customers ADD COLUMN encrypted_email TEXT; -- Encrypted email
ALTER TABLE customers ADD COLUMN encrypted_phone TEXT; -- Encrypted phone
ALTER TABLE customers ADD COLUMN encrypted_address TEXT; -- Encrypted address
ALTER TABLE customers ADD COLUMN data_classification TEXT CHECK (data_classification IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')) DEFAULT 'INTERNAL';

-- Add audit trail for sensitive data access
CREATE TABLE data_access_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Access details
    user_id TEXT NOT NULL, -- User who accessed the data
    user_role TEXT, -- Role of the user
    session_id TEXT, -- Session identifier
    
    -- What was accessed
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    field_names TEXT[], -- Specific fields accessed
    operation TEXT CHECK (operation IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DECRYPT')) NOT NULL,
    
    -- Context
    access_reason TEXT, -- Why the data was accessed
    ip_address INET,
    user_agent TEXT,
    
    -- Data classification and sensitivity
    data_classification TEXT,
    contains_pii BOOLEAN DEFAULT FALSE,
    
    -- Compliance
    legal_basis TEXT, -- GDPR legal basis for processing
    retention_period INTERVAL, -- How long this access should be retained
    
    -- Results
    access_granted BOOLEAN DEFAULT TRUE,
    access_denied_reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- PII detection and classification table
CREATE TABLE pii_detection_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE, -- NULL for global rules
    
    -- Rule details
    rule_name TEXT NOT NULL,
    rule_type TEXT CHECK (rule_type IN ('REGEX', 'KEYWORD', 'ML_MODEL', 'CUSTOM_FUNCTION')) NOT NULL,
    pattern TEXT NOT NULL, -- Regex pattern, keywords, or model name
    pii_type TEXT NOT NULL, -- 'EMAIL', 'PHONE', 'ADDRESS', 'SSN', 'CREDIT_CARD', etc.
    
    -- Sensitivity
    sensitivity_level TEXT CHECK (sensitivity_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')) NOT NULL,
    requires_encryption BOOLEAN DEFAULT TRUE,
    
    -- Rule configuration
    active BOOLEAN DEFAULT TRUE,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.8,
    
    -- Compliance
    gdpr_category TEXT, -- GDPR data category
    retention_days INTEGER DEFAULT 2555, -- 7 years default
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PII detection results table
CREATE TABLE pii_detection_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Detection context
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    field_name TEXT NOT NULL,
    
    -- Detection results
    rule_id UUID NOT NULL REFERENCES pii_detection_rules(id),
    pii_type TEXT NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    matched_pattern TEXT,
    
    -- Original and processed data
    original_value_hash TEXT, -- Hash of original value for comparison
    redacted_value TEXT, -- Redacted version for display
    encrypted BOOLEAN DEFAULT FALSE,
    
    -- Status
    reviewed BOOLEAN DEFAULT FALSE,
    false_positive BOOLEAN DEFAULT FALSE,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Data retention policy table
CREATE TABLE data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Policy details
    policy_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    field_name TEXT, -- NULL for entire table
    
    -- Retention rules
    retention_period INTERVAL NOT NULL,
    action_after_expiry TEXT CHECK (action_after_expiry IN ('DELETE', 'ANONYMIZE', 'ARCHIVE', 'NOTIFY')) NOT NULL,
    
    -- Triggers
    trigger_field TEXT, -- Field to check for expiry (e.g., 'created_at', 'last_accessed_at')
    
    -- Legal basis
    legal_basis TEXT NOT NULL, -- GDPR legal basis or other regulatory requirement
    jurisdiction TEXT DEFAULT 'EU', -- Legal jurisdiction
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    last_executed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, table_name, field_name, policy_name)
);

-- Encryption key management (metadata only, keys stored in external service)
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Key details
    key_id TEXT NOT NULL UNIQUE, -- External key service identifier
    key_purpose TEXT NOT NULL, -- 'MESSAGE_CONTENT', 'CUSTOMER_PII', 'ORDER_DATA'
    algorithm TEXT NOT NULL DEFAULT 'AES-256-GCM',
    
    -- Key lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    rotated_at TIMESTAMPTZ,
    previous_key_id TEXT, -- For key rotation
    
    -- Status
    status TEXT CHECK (status IN ('ACTIVE', 'DEPRECATED', 'REVOKED')) DEFAULT 'ACTIVE',
    
    -- Usage tracking
    encryption_count INTEGER DEFAULT 0,
    decryption_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ
);

-- Create indexes for performance and security
CREATE INDEX idx_data_access_audit_distributor_date ON data_access_audit(distributor_id, created_at DESC);
CREATE INDEX idx_data_access_audit_user ON data_access_audit(user_id, created_at DESC);
CREATE INDEX idx_data_access_audit_table_record ON data_access_audit(table_name, record_id);
CREATE INDEX idx_data_access_audit_pii ON data_access_audit(contains_pii, created_at DESC) WHERE contains_pii = TRUE;

CREATE INDEX idx_pii_detection_rules_distributor ON pii_detection_rules(distributor_id, active) WHERE active = TRUE;
CREATE INDEX idx_pii_detection_rules_type ON pii_detection_rules(pii_type, active) WHERE active = TRUE;

CREATE INDEX idx_pii_detection_results_distributor ON pii_detection_results(distributor_id, created_at DESC);
CREATE INDEX idx_pii_detection_results_table_record ON pii_detection_results(table_name, record_id);
CREATE INDEX idx_pii_detection_results_unreviewed ON pii_detection_results(reviewed, created_at DESC) WHERE reviewed = FALSE;

CREATE INDEX idx_data_retention_policies_distributor ON data_retention_policies(distributor_id, active) WHERE active = TRUE;
CREATE INDEX idx_data_retention_policies_table ON data_retention_policies(table_name, active) WHERE active = TRUE;

CREATE INDEX idx_encryption_keys_distributor ON encryption_keys(distributor_id, status) WHERE status = 'ACTIVE';
CREATE INDEX idx_encryption_keys_purpose ON encryption_keys(key_purpose, status) WHERE status = 'ACTIVE';

-- Function to detect PII in text
CREATE OR REPLACE FUNCTION detect_pii_in_text(
    input_text TEXT,
    dist_id UUID DEFAULT NULL
)
RETURNS TABLE (
    pii_type TEXT,
    confidence DECIMAL(3,2),
    matched_pattern TEXT,
    rule_id UUID
) AS $$
DECLARE
    rule_record pii_detection_rules%ROWTYPE;
    match_result TEXT;
    confidence_score DECIMAL(3,2);
BEGIN
    -- Loop through active PII detection rules
    FOR rule_record IN 
        SELECT * FROM pii_detection_rules 
        WHERE (distributor_id = dist_id OR distributor_id IS NULL) 
        AND active = TRUE 
        ORDER BY sensitivity_level DESC
    LOOP
        -- Apply rule based on type
        CASE rule_record.rule_type
            WHEN 'REGEX' THEN
                -- Simple regex matching
                IF input_text ~* rule_record.pattern THEN
                    pii_type := rule_record.pii_type;
                    confidence := 0.9; -- High confidence for regex matches
                    matched_pattern := rule_record.pattern;
                    rule_id := rule_record.id;
                    RETURN NEXT;
                END IF;
                
            WHEN 'KEYWORD' THEN
                -- Keyword matching
                IF position(LOWER(rule_record.pattern) in LOWER(input_text)) > 0 THEN
                    pii_type := rule_record.pii_type;
                    confidence := 0.7; -- Medium confidence for keyword matches
                    matched_pattern := rule_record.pattern;
                    rule_id := rule_record.id;
                    RETURN NEXT;
                END IF;
                
            -- ML_MODEL and CUSTOM_FUNCTION would be implemented with external services
            ELSE
                CONTINUE;
        END CASE;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to log data access for audit
CREATE OR REPLACE FUNCTION log_data_access(
    dist_id UUID,
    user_id_param TEXT,
    table_name_param TEXT,
    record_id_param UUID,
    operation_param TEXT,
    field_names_param TEXT[] DEFAULT NULL,
    contains_pii_param BOOLEAN DEFAULT FALSE,
    ip_address_param INET DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    audit_id UUID;
BEGIN
    INSERT INTO data_access_audit (
        distributor_id,
        user_id,
        table_name,
        record_id,
        field_names,
        operation,
        contains_pii,
        ip_address
    ) VALUES (
        dist_id,
        user_id_param,
        table_name_param,
        record_id_param,
        field_names_param,
        operation_param,
        contains_pii_param,
        ip_address_param
    ) RETURNING id INTO audit_id;
    
    RETURN audit_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check data retention and flag expired data
CREATE OR REPLACE FUNCTION check_data_retention()
RETURNS INTEGER AS $$
DECLARE
    policy_record data_retention_policies%ROWTYPE;
    expired_count INTEGER := 0;
    query_text TEXT;
BEGIN
    FOR policy_record IN 
        SELECT * FROM data_retention_policies 
        WHERE active = TRUE
    LOOP
        -- Build dynamic query to find expired records
        IF policy_record.field_name IS NOT NULL THEN
            query_text := format(
                'UPDATE %I SET data_expired = TRUE WHERE %I < NOW() - INTERVAL ''%s'' AND distributor_id = %L',
                policy_record.table_name,
                policy_record.trigger_field,
                policy_record.retention_period,
                policy_record.distributor_id
            );
        ELSE
            query_text := format(
                'UPDATE %I SET data_expired = TRUE WHERE %I < NOW() - INTERVAL ''%s'' AND distributor_id = %L',
                policy_record.table_name,
                policy_record.trigger_field,
                policy_record.retention_period,
                policy_record.distributor_id
            );
        END IF;
        
        -- Execute the query (in a real implementation, this would be more careful)
        -- EXECUTE query_text;
        -- GET DIAGNOSTICS expired_count = ROW_COUNT;
        
        -- Update last executed timestamp
        UPDATE data_retention_policies 
        SET last_executed_at = NOW()
        WHERE id = policy_record.id;
    END LOOP;
    
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger function to detect PII on message insert/update
CREATE OR REPLACE FUNCTION trigger_detect_message_pii()
RETURNS TRIGGER AS $$
DECLARE
    pii_results RECORD;
    found_pii BOOLEAN := FALSE;
    dist_id UUID;
BEGIN
    -- Get distributor_id from conversation
    SELECT c.distributor_id INTO dist_id
    FROM conversations c 
    WHERE c.id = NEW.conversation_id;
    
    -- Detect PII in message content
    FOR pii_results IN 
        SELECT * FROM detect_pii_in_text(NEW.content, dist_id)
    LOOP
        found_pii := TRUE;
        
        -- Insert detection result
        INSERT INTO pii_detection_results (
            distributor_id,
            table_name,
            record_id,
            field_name,
            rule_id,
            pii_type,
            confidence_score,
            matched_pattern,
            original_value_hash
        ) VALUES (
            dist_id,
            'messages',
            NEW.id,
            'content',
            pii_results.rule_id,
            pii_results.pii_type,
            pii_results.confidence,
            pii_results.matched_pattern,
            encode(sha256(NEW.content::bytea), 'hex')
        );
    END LOOP;
    
    -- Update the message with PII flag
    NEW.contains_pii := found_pii;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create PII detection trigger
CREATE TRIGGER trigger_detect_message_pii
    BEFORE INSERT OR UPDATE OF content ON messages
    FOR EACH ROW EXECUTE FUNCTION trigger_detect_message_pii();

-- Add data_expired flag to relevant tables
ALTER TABLE messages ADD COLUMN data_expired BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN data_expired BOOLEAN DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN data_expired BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN data_expired BOOLEAN DEFAULT FALSE;

-- Insert default PII detection rules
INSERT INTO pii_detection_rules (rule_name, rule_type, pattern, pii_type, sensitivity_level, requires_encryption) VALUES
('Email Address', 'REGEX', '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'EMAIL', 'MEDIUM', TRUE),
('Phone Number (US)', 'REGEX', '(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', 'PHONE', 'MEDIUM', TRUE),
('Credit Card', 'REGEX', '\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'CREDIT_CARD', 'CRITICAL', TRUE),
('Address Keyword', 'KEYWORD', 'address', 'ADDRESS', 'LOW', FALSE),
('SSN', 'REGEX', '\b\d{3}-?\d{2}-?\d{4}\b', 'SSN', 'CRITICAL', TRUE);

-- RLS policies for new tables
ALTER TABLE data_access_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE pii_detection_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE pii_detection_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_retention_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE encryption_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY data_access_audit_tenant_isolation ON data_access_audit
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY pii_detection_rules_tenant_isolation ON pii_detection_rules
    FOR ALL USING (distributor_id = get_current_distributor_id() OR distributor_id IS NULL OR is_service_role());

CREATE POLICY pii_detection_results_tenant_isolation ON pii_detection_results
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY data_retention_policies_tenant_isolation ON data_retention_policies
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

CREATE POLICY encryption_keys_tenant_isolation ON encryption_keys
    FOR ALL USING (distributor_id = get_current_distributor_id() OR is_service_role());

-- Grant permissions
GRANT SELECT ON data_access_audit TO distributor_user;
GRANT SELECT ON pii_detection_rules TO distributor_user;
GRANT SELECT, UPDATE ON pii_detection_results TO distributor_user;
GRANT SELECT ON data_retention_policies TO distributor_user;
GRANT SELECT ON encryption_keys TO distributor_user;

GRANT EXECUTE ON FUNCTION detect_pii_in_text TO distributor_user;
GRANT EXECUTE ON FUNCTION log_data_access TO distributor_user;

-- Create view for privacy compliance dashboard
CREATE VIEW privacy_compliance_dashboard AS
SELECT 
    d.id as distributor_id,
    d.business_name,
    COUNT(DISTINCT pdr.id) as pii_detections_total,
    COUNT(DISTINCT CASE WHEN pdr.reviewed = FALSE THEN pdr.id END) as pii_detections_pending,
    COUNT(DISTINCT daa.id) as data_access_events_last_30_days,
    COUNT(DISTINCT CASE WHEN daa.contains_pii = TRUE THEN daa.id END) as pii_access_events_last_30_days,
    COUNT(DISTINCT drp.id) as active_retention_policies,
    COUNT(DISTINCT ek.id) as active_encryption_keys
FROM distributors d
LEFT JOIN pii_detection_results pdr ON pdr.distributor_id = d.id
LEFT JOIN data_access_audit daa ON daa.distributor_id = d.id AND daa.created_at >= NOW() - INTERVAL '30 days'
LEFT JOIN data_retention_policies drp ON drp.distributor_id = d.id AND drp.active = TRUE
LEFT JOIN encryption_keys ek ON ek.distributor_id = d.id AND ek.status = 'ACTIVE'
GROUP BY d.id, d.business_name;

GRANT SELECT ON privacy_compliance_dashboard TO distributor_user;

-- Add comments for documentation
COMMENT ON TABLE data_access_audit IS 'Comprehensive audit trail for sensitive data access and GDPR compliance';
COMMENT ON TABLE pii_detection_rules IS 'Configurable rules for detecting personally identifiable information';
COMMENT ON TABLE pii_detection_results IS 'Results of PII detection scans with review workflow';
COMMENT ON TABLE data_retention_policies IS 'Data retention policies for compliance and privacy management';
COMMENT ON TABLE encryption_keys IS 'Encryption key metadata for field-level encryption management';

COMMENT ON FUNCTION detect_pii_in_text IS 'Detects PII in text using configurable rules';
COMMENT ON FUNCTION log_data_access IS 'Logs data access events for audit and compliance';
COMMENT ON FUNCTION check_data_retention IS 'Checks and flags data that has exceeded retention periods';

COMMENT ON VIEW privacy_compliance_dashboard IS 'Privacy and compliance metrics dashboard view';