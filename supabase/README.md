# Reddi Platform Database Migrations

This directory contains Supabase migrations for the complete Reddi platform, supporting Orders, Customers, and Messages functionality with AI agent integration.

## Migration Files Overview

| Migration | Description |
|-----------|-------------|
| `20240716120000_create_customers_table.sql` | Core customers table supporting existing Customer interface |
| `20240716120001_create_customer_labels.sql` | Customer labels system (many-to-many) |
| `20240716120002_create_conversations_table.sql` | Conversations for grouping messages by customer/channel |
| `20240716120003_create_messages_table.sql` | Core messages table with AI processing support |
| `20240716120004_create_orders_table.sql` | Enhanced orders table with AI integration |
| `20240716120005_create_order_products_table.sql` | Order line items (OrderProduct interface) |
| `20240716120006_create_ai_support_tables.sql` | AI responses, templates, products, training data |
| `20240716120007_create_additional_indexes.sql` | Performance indexes for all queries |
| `20240716120008_create_triggers.sql` | Data consistency and real-time update triggers |

## Database Schema Overview

### Core Tables
- **customers**: Business/customer information
- **conversations**: Groups messages by customer and channel
- **messages**: Individual messages with AI processing metadata
- **orders**: Order information with AI generation tracking
- **order_products**: Order line items with AI extraction data

### Support Tables
- **customer_labels** + **customer_label_assignments**: Customer categorization
- **order_attachments**: File attachments for orders
- **ai_responses**: AI agent response tracking
- **message_templates**: Reusable AI response templates
- **products**: Future product catalog
- **ai_training_data**: Data for improving AI performance

## How to Apply Migrations

### Method 1: Using Supabase CLI (Recommended)

1. **Install Supabase CLI**:
   ```bash
   npm install -g supabase
   ```

2. **Initialize Supabase in your project** (if not already done):
   ```bash
   cd /Users/macbook/orderagent
   supabase init
   ```

3. **Link to your remote project**:
   ```bash
   supabase link --project-ref zbybqspipgsntauuapgg
   ```

4. **Apply all migrations**:
   ```bash
   supabase db push
   ```

### Method 2: Using Supabase MCP (Alternative)

If you prefer to use your existing MCP setup:

```python
# Using your Pydantic AI agent with Supabase MCP
for migration_file in migration_files:
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    result = await supabase_mcp.apply_migration(
        name=migration_file.stem,
        query=sql_content
    )
```

### Method 3: Manual Application

Copy and paste each migration file's contents into the Supabase SQL Editor in order.

## Data Flow Integration

### Customer Journey
```
Customer Registration → Messages → AI Processing → Orders → Review → Confirmation
```

### Key Relationships
- `customers` ← `conversations` ← `messages`
- `customers` ← `orders` ← `order_products`
- `messages` → `ai_responses` (AI processing tracking)
- `conversations` ↔ `orders` (optional linking)

### AI Agent Integration Points

1. **Message Analysis**: `messages.ai_processed` tracks which messages need AI processing
2. **Order Generation**: `orders.ai_generated` marks AI-created orders
3. **Quality Tracking**: `ai_responses` table tracks AI performance
4. **Context Management**: `conversations.ai_context_summary` for conversation context

## TypeScript Interface Mapping

### Existing Interfaces Supported
- ✅ `Customer` → `customers` table
- ✅ `CustomerLabel` → `customer_labels` + `customer_label_assignments`
- ✅ `Order` → `orders` table
- ✅ `OrderProduct` → `order_products` table
- ✅ `OrderDetails` → `orders` + `order_products` + `order_attachments`

### New Interfaces Needed
- `Message` → `messages` table
- `Conversation` → `conversations` table
- `AIResponse` → `ai_responses` table

## Performance Considerations

### Indexes Created
- **Full-text search**: Customer names, order comments, message content
- **Filtering**: Status-based filtering for all main tables
- **Sorting**: Date-based sorting with composite indexes
- **Foreign keys**: All relationships properly indexed

### Triggers for Real-time Updates
- **Customer stats**: Auto-updated when orders change
- **Conversation metadata**: Auto-updated when messages are added
- **Order totals**: Auto-calculated from line items
- **Unread counts**: Auto-updated when messages are marked as read

## Environment Setup

After applying migrations, update your environment:

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_key
```

## Testing the Schema

### 1. Verify Tables Created
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

### 2. Test Customer Creation
```sql
INSERT INTO customers (business_name, customer_code, email) 
VALUES ('Test Business', 'TEST001', 'test@example.com');
```

### 3. Test Conversation and Message Flow
```sql
-- Create conversation
INSERT INTO conversations (customer_id, channel) 
VALUES ((SELECT id FROM customers WHERE customer_code = 'TEST001'), 'WHATSAPP');

-- Add message
INSERT INTO messages (conversation_id, content, is_from_customer) 
VALUES ((SELECT id FROM conversations WHERE customer_id = (SELECT id FROM customers WHERE customer_code = 'TEST001')), 
        'I need 10 kg of tomatoes', TRUE);
```

## Next Steps

1. **Apply migrations** using your preferred method
2. **Update TypeScript types** to match database schema
3. **Implement Pydantic AI agents** using your agent-platform framework
4. **Create API routes** for frontend integration
5. **Build Messages page UI** with real data

## Troubleshooting

### Common Issues
- **Permission errors**: Ensure your Supabase access token has proper permissions
- **Constraint violations**: Check data consistency if migrations fail
- **Performance issues**: Monitor query performance and adjust indexes as needed

### Rollback Strategy
```bash
# If you need to rollback migrations
supabase db reset
```

**Note**: This will destroy all data. Use with caution in production.