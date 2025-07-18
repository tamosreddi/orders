# Setup Guide - Messages Page Development Environment

## Prerequisites

Before setting up the Messages page, ensure you have:

- Node.js 18+ and npm/pnpm installed
- Python 3.9+ with pip and virtual environment support
- Supabase project already configured (database tables created)
- OpenAI API key for AI agent functionality
- Access to your existing `agent-platform/` framework

## Environment Variables

### Frontend (.env.local)

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# OpenAI (for client-side AI features - optional)
NEXT_PUBLIC_OPENAI_MODEL=gpt-4
```

### Backend (.env)

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4096

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_ACCESS_TOKEN=your_supabase_access_token

# Database Configuration (for MCP)
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Security
JWT_SECRET=your_jwt_secret_key
ENCRYPTION_KEY=your_message_encryption_key

# AI Configuration
AI_CONFIDENCE_THRESHOLD=0.8
AI_BUDGET_LIMIT_USD=1000
AI_MAX_RETRIES=3

# External Integrations
WHATSAPP_WEBHOOK_SECRET=your_whatsapp_webhook_secret
SMS_PROVIDER_API_KEY=your_sms_provider_key
EMAIL_PROVIDER_API_KEY=your_email_provider_key

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Frontend Dependencies

### Install Required Packages

```bash
# Core Supabase dependencies (if not already installed)
npm install @supabase/supabase-js @supabase/ssr

# Real-time and API communication
npm install socket.io-client @tanstack/react-query
npm install axios swr

# UI components (if not already installed)
npm install @headlessui/react lucide-react

# WebSocket and real-time features
npm install ws @types/ws

# Form handling and validation
npm install react-hook-form @hookform/resolvers zod

# Development dependencies
npm install -D @types/node @types/react
```

### Verify Existing Dependencies

Ensure these are already in your package.json:
```json
{
  "dependencies": {
    "next": "14.x",
    "react": "18.x",
    "tailwindcss": "3.x",
    "@tanstack/react-table": "8.x",
    "clsx": "^2.0.0"
  }
}
```

## Backend Dependencies

### Python Virtual Environment Setup

```bash
# Create virtual environment (if not exists)
python -m venv venv_linux

# Activate virtual environment
source venv_linux/bin/activate  # Linux/Mac
# or
venv_linux\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

### Install Backend Packages

```bash
# Core FastAPI and Pydantic AI (from your agent-platform)
pip install fastapi uvicorn pydantic-ai mcp

# Database and Supabase integration
pip install supabase asyncpg sqlalchemy

# AI and OpenAI integration
pip install openai python-dotenv

# Security and authentication
pip install python-jose[cryptography] passlib bcrypt

# Real-time and WebSocket support
pip install websockets fastapi-websocket

# External integrations
pip install requests httpx aiohttp

# Development and testing
pip install pytest pytest-asyncio black isort mypy

# Additional utilities
pip install pydantic[email] email-validator
```

### Agent Platform Dependencies

```bash
# Ensure your agent-platform dependencies are installed
cd agent-platform
pip install -r requirements.txt
cd ..
```

## MCP Configuration Setup

### Verify MCP Configuration

Your MCP setup should already be configured in:

1. **Agent Platform MCP Config** (`/agent-platform/mcp_config.json`):
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-supabase"],
      "env": {
        "SUPABASE_URL": "your_supabase_url",
        "SUPABASE_ANON_KEY": "your_anon_key"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "your_context7_key"
      }
    }
  }
}
```

2. **Claude Code MCP Config** (`/.mcp.json`):
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-supabase"],
      "env": {
        "SUPABASE_URL": "your_supabase_url",
        "SUPABASE_ANON_KEY": "your_anon_key"
      }
    }
  }
}
```

## Database Setup

### Verify Database Tables

Ensure these tables exist in your Supabase database:

```bash
# Check if migrations are applied
supabase db push

# Generate TypeScript types (if needed)
supabase gen types typescript --local > types/database.ts
```

**Required Tables:**
- `distributors` - Multi-tenant business accounts
- `customers` - Customer information with distributor isolation
- `conversations` - Chat conversations grouped by customer/channel
- `messages` - Individual messages with AI processing metadata
- `orders` - Orders with AI generation tracking
- `order_products` - Order line items
- `ai_responses` - AI agent response tracking
- `ai_usage_metrics` - AI usage and cost monitoring
- `products` - Product catalog (if applicable)

### Database Verification Script

```bash
# Test database connection
python -c "
import asyncio
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase = create_client(url, key)

try:
    result = supabase.table('distributors').select('id').limit(1).execute()
    print('✅ Database connection successful')
    print(f'Tables accessible: {len(result.data) >= 0}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

## Development Setup

### 1. Backend Server Setup

```bash
# Navigate to backend directory (create if needed)
mkdir -p backend
cd backend

# Create main FastAPI application
touch main.py

# Create directory structure
mkdir -p {routers,agents,models,services,config}

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Development Server

```bash
# Navigate to project root
cd /Users/macbook/orderagent

# Start Next.js development server
npm run dev
# or
pnpm dev
```

### 3. Agent Platform Integration

```bash
# Test agent platform connectivity
cd agent-platform
python -c "
from agent_template import get_pydantic_ai_agent
import asyncio

async def test():
    try:
        client, agent = await get_pydantic_ai_agent()
        print('✅ Agent platform ready')
        return True
    except Exception as e:
        print(f'❌ Agent platform error: {e}')
        return False

asyncio.run(test())
"
```

## Development Workflow

### 1. Start Development Environment

```bash
# Terminal 1: Backend server
cd backend
source ../venv_linux/bin/activate
uvicorn main:app --reload

# Terminal 2: Frontend server
npm run dev

# Terminal 3: Database (if running locally)
supabase start
```

### 2. Verify Setup

**Frontend Check:**
- Visit `http://localhost:3000`
- Verify existing Orders and Customers pages work
- Check browser console for errors

**Backend Check:**
- Visit `http://localhost:8000/docs` for FastAPI documentation
- Test API endpoints via Swagger UI

**Database Check:**
- Access Supabase dashboard
- Verify tables and data exist
- Check RLS policies are active

### 3. Development Tools

**Code Quality:**
```bash
# Frontend linting
npm run lint
npm run type-check

# Backend formatting
cd backend
black .
isort .
mypy .
```

**Testing:**
```bash
# Frontend tests
npm run test

# Backend tests
cd backend
pytest
```

## Troubleshooting

### Common Issues

**1. MCP Connection Errors:**
```bash
# Verify MCP servers are accessible
npx @modelcontextprotocol/inspector
```

**2. Database Connection Issues:**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Test direct connection
psql $DATABASE_URL -c "SELECT 1;"
```

**3. OpenAI API Issues:**
```bash
# Test OpenAI connectivity
python -c "
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Hello'}],
    max_tokens=5
)
print('✅ OpenAI API working')
"
```

**4. Frontend Build Issues:**
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

**5. Python Dependencies:**
```bash
# Reinstall all dependencies
pip freeze > requirements.txt
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Environment Validation Script

```bash
# Run this script to validate your setup
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    'OPENAI_API_KEY',
    'SUPABASE_URL', 
    'SUPABASE_ANON_KEY',
    'DATABASE_URL'
]

print('Environment Variable Check:')
for var in required_vars:
    value = os.getenv(var)
    status = '✅' if value else '❌'
    print(f'{status} {var}: {\"Set\" if value else \"Missing\"}')
"
```

## Production Deployment

### Environment Setup

**Frontend (Vercel/Netlify):**
- Set all `NEXT_PUBLIC_*` environment variables
- Configure build command: `npm run build`
- Set output directory: `.next`

**Backend (Railway/Heroku/DigitalOcean):**
- Set all backend environment variables
- Configure start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Ensure Python version matches development

**Database (Supabase Production):**
- Apply all migrations: `supabase db push`
- Configure RLS policies for production
- Set up proper backup schedule
- Monitor usage and performance

### Security Checklist

- [ ] All environment variables properly set
- [ ] No secrets in code or version control
- [ ] CORS properly configured for production domains
- [ ] JWT secrets are strong and unique
- [ ] Database RLS policies tested and active
- [ ] API rate limiting configured
- [ ] HTTPS enabled for all endpoints
- [ ] Webhook endpoints secured with proper validation

### Monitoring Setup

**Application Monitoring:**
- Set up error tracking (Sentry, Bugsnag)
- Configure performance monitoring
- Set up uptime monitoring

**AI Usage Monitoring:**
- Monitor OpenAI API costs via database
- Set up budget alerts
- Track agent performance metrics
- Monitor response quality scores