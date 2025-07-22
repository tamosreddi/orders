# Supabase Connection Guide

This guide explains the two different ways to connect to Supabase in this project and how to set them up.

## Overview: Two Types of Connections

### 1. Supabase MCP (Model Context Protocol) Connection
- **Purpose**: Allows Claude Code AI assistant to directly interact with your Supabase database
- **Use Case**: Database management, queries, migrations, and administrative tasks through AI
- **Scope**: Available only to Claude Code during development/debugging sessions
- **Access**: Full database access including schema changes, data queries, and project management

### 2. JavaScript/Supabase-JS Connection  
- **Purpose**: Allows your Next.js application to interact with Supabase from the frontend/backend
- **Use Case**: User authentication, data fetching, real-time subscriptions in your web app
- **Scope**: Used by your actual application code and end users
- **Access**: Controlled by Row Level Security (RLS) policies and API permissions

## Key Differences

| Aspect | MCP Connection | JavaScript Connection |
|--------|---------------|---------------------|
| **Who uses it** | Claude Code AI | Your application & users |
| **When active** | Only during AI sessions | Always (when app is running) |
| **Permissions** | Full admin access | Limited by RLS policies |
| **Configuration** | `.mcp.json` file | Environment variables |
| **Purpose** | Development & management | Production functionality |

## Setup Instructions

### Setting Up Supabase MCP Connection

1. **Install Claude Code with MCP support** (if not already done):
   ```bash
   # Make sure you have Claude Code installed with MCP capabilities
   ```

2. **Configure MCP in your project**:
   Create/update `.mcp.json` in your project root:
   ```json
   {
     "mcpServers": {
       "supabase": {
         "command": "npx",
         "args": ["@modelcontextprotocol/server-supabase"],
         "env": {
           "SUPABASE_URL": "https://your-project.supabase.co",
           "SUPABASE_SERVICE_ROLE_KEY": "your-service-role-key"
         }
       }
     }
   }
   ```

3. **Get your credentials from Supabase Dashboard**:
   - Go to your Supabase project dashboard
   - Navigate to Settings → API
   - Copy the "Project URL" and "Service Role Key" (not the anon key)

4. **Test the connection**:
   ```bash
   # In Claude Code, test with:
   # mcp__supabase__get_project_url
   ```

### Setting Up JavaScript Connection

1. **Install Supabase JS client** (already done in this project):
   ```bash
   npm install @supabase/supabase-js
   ```

2. **Create environment variables**:
   Create `.env.local` file in your project root:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   ```

3. **Create Supabase client configuration**:
   ```typescript
   // lib/supabase/client.ts
   import { createClient } from '@supabase/supabase-js'

   const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
   const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

   export const supabase = createClient(supabaseUrl, supabaseAnonKey)
   ```

4. **Use in your components**:
   ```typescript
   import { supabase } from '@/lib/supabase/client'

   // Example: Fetch data
   const { data, error } = await supabase
     .from('customers')
     .select('*')
   ```

## Troubleshooting Connection Issues

### MCP Connection Issues

**Problem**: `mcp__supabase__*` tools not working

**Solutions**:
1. Check `.mcp.json` configuration
2. Verify service role key is correct (not anon key)
3. Restart Claude Code session
4. Check project URL format

**Verification Commands**:
```bash
# Test these in Claude Code:
mcp__supabase__get_project_url
mcp__supabase__list_tables
```

### JavaScript Connection Issues

**Problem**: Supabase client errors in application

**Solutions**:
1. Check `.env.local` file exists and has correct values
2. Verify anon key is correct (not service role key)
3. Check RLS policies are properly configured
4. Restart development server

**Verification Code**:
```typescript
// Test in your app
console.log('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)
console.log('Supabase Key exists:', !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY)

// Test connection
const { data, error } = await supabase.from('customers').select('count')
console.log('Connection test:', { data, error })
```

## Security Notes

### For MCP Connection:
- **Service Role Key**: Has full database access - keep secure
- Only used during development with Claude Code
- Should not be committed to version control
- Add `.mcp.json` to `.gitignore` if it contains secrets

### For JavaScript Connection:
- **Anon Key**: Safe to expose in frontend code
- Access controlled by Row Level Security (RLS) policies
- Environment variables should not be committed
- Add `.env.local` to `.gitignore`

## Current Project Status

### ✅ MCP Connection
- Status: **Connected and working**
- Project URL: `https://ckapulfmocievprlnzux.supabase.co`
- Tables accessible: 43 tables including `customers`

### ✅ JavaScript Connection  
- Status: **Configured**
- Package: `@supabase/supabase-js: ^2.52.0` installed
- Client setup: Ready for implementation

## Quick Reference

### When to use MCP tools:
- Database schema changes
- Running SQL queries for debugging
- Managing migrations
- Checking table structures
- Administrative tasks

### When to use JavaScript client:
- User authentication in your app
- Fetching data for components
- Real-time subscriptions
- User-facing database operations
- Production functionality

---

*Last updated: 2025-01-19*