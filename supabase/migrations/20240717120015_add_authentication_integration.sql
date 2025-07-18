-- Add complete authentication integration with Supabase Auth
-- Links native Supabase authentication to the business logic and distributor system
-- Provides role-based access control and team management capabilities

-- User profiles table (links auth.users to distributors)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- User details
    first_name TEXT,
    last_name TEXT,
    display_name TEXT, -- Computed: first_name + last_name or custom
    avatar_url TEXT,
    
    -- Role and permissions
    role TEXT CHECK (role IN ('OWNER', 'ADMIN', 'MANAGER', 'OPERATOR')) NOT NULL DEFAULT 'OPERATOR',
    permissions JSONB DEFAULT '[]'::jsonb, -- Array of specific permissions
    
    -- Status
    status TEXT CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING')) DEFAULT 'PENDING',
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- Activity tracking
    last_sign_in_at TIMESTAMPTZ,
    last_activity_at TIMESTAMPTZ,
    sign_in_count INTEGER DEFAULT 0,
    
    -- Preferences
    timezone TEXT DEFAULT 'UTC',
    locale TEXT DEFAULT 'en',
    notification_preferences JSONB DEFAULT '{
        "email_notifications": true,
        "push_notifications": true,
        "sms_notifications": false,
        "order_alerts": true,
        "ai_alerts": true,
        "system_alerts": true
    }'::jsonb,
    
    -- Onboarding
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step TEXT, -- Track where user is in onboarding process
    
    -- Security
    require_password_change BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, id)
);

-- User invitations table
CREATE TABLE user_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Invitation details
    email TEXT NOT NULL,
    role TEXT CHECK (role IN ('ADMIN', 'MANAGER', 'OPERATOR')) NOT NULL,
    permissions JSONB DEFAULT '[]'::jsonb,
    
    -- Invitation metadata
    invited_by UUID REFERENCES user_profiles(id),
    invitation_token TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'base64'),
    
    -- Status and expiry
    status TEXT CHECK (status IN ('PENDING', 'ACCEPTED', 'EXPIRED', 'REVOKED')) DEFAULT 'PENDING',
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days',
    
    -- Usage tracking
    sent_count INTEGER DEFAULT 0,
    last_sent_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES user_profiles(id),
    
    -- Personal message
    personal_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, email, status) -- Prevent duplicate pending invitations
);

-- Role permissions mapping
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID REFERENCES distributors(id) ON DELETE CASCADE, -- NULL for global defaults
    
    -- Role definition
    role TEXT NOT NULL,
    permission_name TEXT NOT NULL, -- 'customers.read', 'orders.write', 'ai.manage', etc.
    permission_scope TEXT DEFAULT 'all', -- 'all', 'own', 'team', etc.
    
    -- Permission details
    description TEXT,
    category TEXT, -- 'customers', 'orders', 'messages', 'ai', 'admin'
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(distributor_id, role, permission_name)
);

-- User sessions tracking (enhanced beyond Supabase default)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    
    -- Session details
    session_token TEXT, -- Reference to Supabase session if needed
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    
    -- Location (if enabled)
    country TEXT,
    city TEXT,
    
    -- Session timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    
    -- Session metadata
    login_method TEXT, -- 'email', 'google', 'magic_link', etc.
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_user_profiles_distributor ON user_profiles(distributor_id, status);
CREATE INDEX idx_user_profiles_role ON user_profiles(role, status);
CREATE INDEX idx_user_profiles_email_verified ON user_profiles(email_verified, status);

CREATE INDEX idx_user_invitations_distributor ON user_invitations(distributor_id, status);
CREATE INDEX idx_user_invitations_email ON user_invitations(email, status);
CREATE INDEX idx_user_invitations_token ON user_invitations(invitation_token);
CREATE INDEX idx_user_invitations_expires ON user_invitations(expires_at) WHERE status = 'PENDING';

CREATE INDEX idx_role_permissions_distributor ON role_permissions(distributor_id, role);
CREATE INDEX idx_role_permissions_category ON role_permissions(category, active) WHERE active = TRUE;

CREATE INDEX idx_user_sessions_user_profile ON user_sessions(user_profile_id, started_at DESC);
CREATE INDEX idx_user_sessions_distributor ON user_sessions(distributor_id, started_at DESC);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active, last_activity_at DESC) WHERE is_active = TRUE;

-- Enhanced authentication functions

-- Function to get current user profile
CREATE OR REPLACE FUNCTION get_current_user_profile()
RETURNS user_profiles AS $$
DECLARE
    profile_record user_profiles%ROWTYPE;
BEGIN
    SELECT * INTO profile_record 
    FROM user_profiles 
    WHERE id = auth.uid();
    
    RETURN profile_record;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enhanced function to get current distributor ID using auth
CREATE OR REPLACE FUNCTION get_current_distributor_id()
RETURNS UUID AS $$
BEGIN
    -- First try to get from user profile (proper auth-based approach)
    RETURN (
        SELECT distributor_id 
        FROM user_profiles 
        WHERE id = auth.uid() 
        AND status = 'ACTIVE'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has permission
CREATE OR REPLACE FUNCTION user_has_permission(
    permission_name_param TEXT,
    scope_param TEXT DEFAULT 'all'
)
RETURNS BOOLEAN AS $$
DECLARE
    user_profile user_profiles%ROWTYPE;
    has_permission BOOLEAN := FALSE;
BEGIN
    -- Get current user profile
    user_profile := get_current_user_profile();
    
    IF user_profile.id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- OWNER role has all permissions
    IF user_profile.role = 'OWNER' THEN
        RETURN TRUE;
    END IF;
    
    -- Check role-based permissions
    SELECT EXISTS(
        SELECT 1 FROM role_permissions 
        WHERE (distributor_id = user_profile.distributor_id OR distributor_id IS NULL)
        AND role = user_profile.role
        AND permission_name = permission_name_param
        AND (permission_scope = scope_param OR permission_scope = 'all')
        AND active = TRUE
    ) INTO has_permission;
    
    -- Check individual user permissions override
    IF NOT has_permission THEN
        has_permission := user_profile.permissions ? permission_name_param;
    END IF;
    
    RETURN has_permission;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create user profile on first sign in
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    invitation_record user_invitations%ROWTYPE;
    default_distributor_id UUID;
BEGIN
    -- Check if user was invited
    SELECT * INTO invitation_record
    FROM user_invitations 
    WHERE email = NEW.email 
    AND status = 'PENDING' 
    AND expires_at > NOW()
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF FOUND THEN
        -- User was invited - create profile with invited role
        INSERT INTO user_profiles (
            id,
            distributor_id,
            first_name,
            last_name,
            role,
            permissions,
            status,
            email_verified
        ) VALUES (
            NEW.id,
            invitation_record.distributor_id,
            COALESCE(NEW.raw_user_meta_data->>'first_name', ''),
            COALESCE(NEW.raw_user_meta_data->>'last_name', ''),
            invitation_record.role,
            invitation_record.permissions,
            'ACTIVE',
            NEW.email_confirmed_at IS NOT NULL
        );
        
        -- Mark invitation as accepted
        UPDATE user_invitations 
        SET status = 'ACCEPTED', accepted_at = NOW()
        WHERE id = invitation_record.id;
        
    ELSE
        -- No invitation - check if this is first user (becomes owner of new distributor)
        SELECT COUNT(*) FROM distributors INTO default_distributor_id;
        
        IF default_distributor_id = 0 THEN
            -- First user ever - create default distributor and make them owner
            INSERT INTO distributors (
                business_name,
                contact_email,
                status,
                onboarding_completed
            ) VALUES (
                'Default Organization',
                NEW.email,
                'PENDING_SETUP',
                FALSE
            ) RETURNING id INTO default_distributor_id;
            
            INSERT INTO user_profiles (
                id,
                distributor_id,
                first_name,
                last_name,
                role,
                status,
                email_verified
            ) VALUES (
                NEW.id,
                default_distributor_id,
                COALESCE(NEW.raw_user_meta_data->>'first_name', ''),
                COALESCE(NEW.raw_user_meta_data->>'last_name', ''),
                'OWNER',
                'ACTIVE',
                NEW.email_confirmed_at IS NOT NULL
            );
        ELSE
            -- Uninvited user - create pending profile (admin needs to approve)
            SELECT id INTO default_distributor_id FROM distributors LIMIT 1;
            
            INSERT INTO user_profiles (
                id,
                distributor_id,
                first_name,
                last_name,
                role,
                status,
                email_verified
            ) VALUES (
                NEW.id,
                default_distributor_id,
                COALESCE(NEW.raw_user_meta_data->>'first_name', ''),
                COALESCE(NEW.raw_user_meta_data->>'last_name', ''),
                'OPERATOR',
                'PENDING', -- Requires admin approval
                NEW.email_confirmed_at IS NOT NULL
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to track user activity
CREATE OR REPLACE FUNCTION track_user_activity()
RETURNS TRIGGER AS $$
DECLARE
    profile_id UUID;
    dist_id UUID;
BEGIN
    -- Get user profile info
    SELECT id, distributor_id INTO profile_id, dist_id
    FROM user_profiles 
    WHERE id = auth.uid();
    
    IF FOUND THEN
        -- Update last activity
        UPDATE user_profiles 
        SET last_activity_at = NOW()
        WHERE id = profile_id;
        
        -- Update session if exists
        UPDATE user_sessions 
        SET last_activity_at = NOW()
        WHERE user_profile_id = profile_id 
        AND is_active = TRUE;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to send invitation email (placeholder for external integration)
CREATE OR REPLACE FUNCTION send_invitation_email(invitation_id UUID)
RETURNS VOID AS $$
DECLARE
    invitation_record user_invitations%ROWTYPE;
    distributor_record distributors%ROWTYPE;
    inviter_record user_profiles%ROWTYPE;
BEGIN
    -- Get invitation details
    SELECT * INTO invitation_record FROM user_invitations WHERE id = invitation_id;
    SELECT * INTO distributor_record FROM distributors WHERE id = invitation_record.distributor_id;
    SELECT * INTO inviter_record FROM user_profiles WHERE id = invitation_record.invited_by;
    
    -- Here you would integrate with an email service
    -- For now, we'll just update the sent count
    UPDATE user_invitations 
    SET sent_count = sent_count + 1, last_sent_at = NOW()
    WHERE id = invitation_id;
    
    -- Log the activity
    INSERT INTO data_access_audit (
        distributor_id,
        user_id,
        table_name,
        record_id,
        operation,
        access_reason
    ) VALUES (
        invitation_record.distributor_id,
        current_user,
        'user_invitations',
        invitation_id,
        'SEND_EMAIL',
        'Invitation email sent'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create triggers for authentication
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Create activity tracking triggers on key tables
CREATE TRIGGER track_activity_customers
    AFTER INSERT OR UPDATE OR DELETE ON customers
    FOR EACH ROW EXECUTE FUNCTION track_user_activity();

CREATE TRIGGER track_activity_orders
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION track_user_activity();

CREATE TRIGGER track_activity_messages
    AFTER INSERT OR UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION track_user_activity();

-- Update existing RLS policies to be authentication-aware

-- Enhanced RLS policy for distributors (users can only see their own distributor)
DROP POLICY IF EXISTS distributors_tenant_isolation ON distributors;
CREATE POLICY distributors_tenant_isolation ON distributors
    FOR ALL USING (
        id = get_current_distributor_id() OR 
        is_service_role() OR
        auth.uid() IN (SELECT id FROM user_profiles WHERE distributor_id = distributors.id AND role = 'OWNER')
    );

-- Add RLS policies for new authentication tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_profiles_own_profile ON user_profiles
    FOR ALL USING (
        id = auth.uid() OR 
        (distributor_id = get_current_distributor_id() AND user_has_permission('users.read')) OR
        is_service_role()
    );

CREATE POLICY user_invitations_distributor_isolation ON user_invitations
    FOR ALL USING (
        distributor_id = get_current_distributor_id() OR is_service_role()
    );

CREATE POLICY user_invitations_insert_policy ON user_invitations
    FOR INSERT WITH CHECK (
        distributor_id = get_current_distributor_id() AND 
        user_has_permission('users.invite')
    );

CREATE POLICY role_permissions_read_policy ON role_permissions
    FOR SELECT USING (
        distributor_id = get_current_distributor_id() OR 
        distributor_id IS NULL OR 
        is_service_role()
    );

CREATE POLICY user_sessions_own_sessions ON user_sessions
    FOR ALL USING (
        user_profile_id = auth.uid() OR
        (distributor_id = get_current_distributor_id() AND user_has_permission('users.read')) OR
        is_service_role()
    );

-- Insert default role permissions
INSERT INTO role_permissions (role, permission_name, permission_scope, description, category) VALUES
-- OWNER permissions (has everything via code logic)
('OWNER', 'all', 'all', 'Full system access', 'admin'),

-- ADMIN permissions
('ADMIN', 'customers.read', 'all', 'View all customers', 'customers'),
('ADMIN', 'customers.write', 'all', 'Create and edit customers', 'customers'),
('ADMIN', 'customers.delete', 'all', 'Delete customers', 'customers'),
('ADMIN', 'orders.read', 'all', 'View all orders', 'orders'),
('ADMIN', 'orders.write', 'all', 'Create and edit orders', 'orders'),
('ADMIN', 'orders.delete', 'all', 'Delete orders', 'orders'),
('ADMIN', 'messages.read', 'all', 'View all messages', 'messages'),
('ADMIN', 'messages.write', 'all', 'Send and edit messages', 'messages'),
('ADMIN', 'ai.read', 'all', 'View AI metrics and responses', 'ai'),
('ADMIN', 'ai.configure', 'all', 'Configure AI settings', 'ai'),
('ADMIN', 'users.read', 'all', 'View all users', 'admin'),
('ADMIN', 'users.invite', 'all', 'Invite new users', 'admin'),
('ADMIN', 'users.manage', 'all', 'Manage user roles and permissions', 'admin'),
('ADMIN', 'settings.read', 'all', 'View system settings', 'admin'),
('ADMIN', 'settings.write', 'all', 'Modify system settings', 'admin'),

-- MANAGER permissions
('MANAGER', 'customers.read', 'all', 'View all customers', 'customers'),
('MANAGER', 'customers.write', 'all', 'Create and edit customers', 'customers'),
('MANAGER', 'orders.read', 'all', 'View all orders', 'orders'),
('MANAGER', 'orders.write', 'all', 'Create and edit orders', 'orders'),
('MANAGER', 'messages.read', 'all', 'View all messages', 'messages'),
('MANAGER', 'messages.write', 'all', 'Send and edit messages', 'messages'),
('MANAGER', 'ai.read', 'all', 'View AI metrics and responses', 'ai'),
('MANAGER', 'users.read', 'team', 'View team members', 'admin'),

-- OPERATOR permissions
('OPERATOR', 'customers.read', 'all', 'View customers', 'customers'),
('OPERATOR', 'orders.read', 'all', 'View orders', 'orders'),
('OPERATOR', 'orders.write', 'own', 'Create and edit own orders', 'orders'),
('OPERATOR', 'messages.read', 'all', 'View messages', 'messages'),
('OPERATOR', 'messages.write', 'all', 'Send messages', 'messages'),
('OPERATOR', 'ai.read', 'basic', 'View basic AI information', 'ai');

-- Add updated_at triggers for new tables
CREATE TRIGGER trigger_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to distributor_user role
GRANT SELECT, UPDATE ON user_profiles TO distributor_user;
GRANT SELECT, INSERT, UPDATE ON user_invitations TO distributor_user;
GRANT SELECT ON role_permissions TO distributor_user;
GRANT SELECT, INSERT ON user_sessions TO distributor_user;

GRANT EXECUTE ON FUNCTION get_current_user_profile TO distributor_user;
GRANT EXECUTE ON FUNCTION user_has_permission TO distributor_user;
GRANT EXECUTE ON FUNCTION send_invitation_email TO distributor_user;

-- Create view for user management dashboard
CREATE VIEW user_management_dashboard AS
SELECT 
    up.id,
    up.first_name,
    up.last_name,
    up.display_name,
    up.role,
    up.status,
    up.email_verified,
    up.last_sign_in_at,
    up.last_activity_at,
    up.sign_in_count,
    up.onboarding_completed,
    up.created_at,
    d.business_name as distributor_name,
    -- Active session count
    (SELECT COUNT(*) FROM user_sessions us WHERE us.user_profile_id = up.id AND us.is_active = TRUE) as active_sessions,
    -- Permissions summary
    (SELECT COUNT(*) FROM role_permissions rp WHERE rp.role = up.role AND rp.active = TRUE) as permission_count
FROM user_profiles up
JOIN distributors d ON d.id = up.distributor_id;

GRANT SELECT ON user_management_dashboard TO distributor_user;

-- Add comments for documentation
COMMENT ON TABLE user_profiles IS 'User profiles linking Supabase Auth to distributors with role-based permissions';
COMMENT ON TABLE user_invitations IS 'User invitation system for team management';
COMMENT ON TABLE role_permissions IS 'Role-based permission system for fine-grained access control';
COMMENT ON TABLE user_sessions IS 'Enhanced user session tracking beyond Supabase defaults';

COMMENT ON FUNCTION get_current_user_profile IS 'Returns the current authenticated user profile';
COMMENT ON FUNCTION user_has_permission IS 'Checks if current user has a specific permission';
COMMENT ON FUNCTION handle_new_user IS 'Creates user profile when new user signs up or accepts invitation';
COMMENT ON FUNCTION track_user_activity IS 'Tracks user activity across the platform';

COMMENT ON VIEW user_management_dashboard IS 'Comprehensive user management dashboard for administrators';