# Database Setup for WhatsApp Integration

This directory contains the database migrations and schema definitions required for the WhatsApp integration feature.

## Prerequisites

- Supabase project set up and configured
- Database connection established
- Admin access to run migrations

## Applying Migrations

### Option 1: Using Supabase Dashboard (Recommended)

1. Open your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `migrations/001_create_conversations_messages.sql`
4. Run the SQL migration
5. Verify the tables were created successfully

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Initialize Supabase in your project (if not done)
supabase init

# Link to your remote project
supabase link --project-ref YOUR_PROJECT_REF

# Apply the migration
supabase db push --db-url YOUR_DATABASE_URL < database/migrations/001_create_conversations_messages.sql
```

### Option 3: Using psql directly

```bash
psql YOUR_DATABASE_URL < database/migrations/001_create_conversations_messages.sql
```

## Tables Created

The migration creates the following tables:

### `conversations`
- Stores conversation records between customers and distributors
- Supports multiple channels: WhatsApp, SMS, Email
- Includes AI context summaries and unread counts
- Row Level Security (RLS) enabled for multi-tenant isolation

### `messages`
- Stores individual messages within conversations
- Supports different message types: Text, Media, Audio, File
- Includes AI processing fields for future AI features
- External message ID tracking for Twilio integration
- Row Level Security (RLS) enabled for data isolation

## Indexes Created

Performance indexes are automatically created for:
- Customer and distributor lookups
- Channel filtering
- Message timestamps
- AI processing status
- External message ID lookups

## Row Level Security (RLS)

Both tables have RLS policies that ensure:
- Distributors can only access their own conversations and messages
- Data isolation is maintained across different distributor accounts
- Secure API access through Supabase client

## Verification

After running the migration, verify the setup:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('conversations', 'messages');

-- Check RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('conversations', 'messages');

-- Check indexes
SELECT indexname, tablename FROM pg_indexes 
WHERE tablename IN ('conversations', 'messages');
```

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure you have admin/owner access to the database
2. **Table already exists**: The migration uses `CREATE TABLE IF NOT EXISTS` so it's safe to run multiple times
3. **Foreign key violations**: Ensure the `customers` and `distributors` tables exist first

### Manual Cleanup (if needed)

```sql
-- Drop tables in correct order (if you need to start over)
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
```

## Next Steps

After applying the migration:

1. Update your TypeScript types (already done in `lib/supabase/types.ts`)
2. Test the WhatsApp webhook integration
3. Verify message persistence through the UI
4. Set up proper environment variables for Twilio

For additional help, refer to the main README.md file in the project root.