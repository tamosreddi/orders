# 📚 Database Schema Guide - AI-Powered Order Management Platform

**A complete guide for engineers to understand our database architecture**

## 🎯 **Overview**

This platform is a **multi-tenant B2B order management system** with AI-powered message processing. The database supports:

- **Multi-channel communication** (WhatsApp, SMS, Email)
- **AI agents** for natural language order processing
- **Multi-tenant architecture** with distributor isolation
- **Enterprise security** with RLS and encryption
- **Real-time messaging** and webhook integrations

---

## 🏗️ **Core Architecture**

### **Multi-Tenant Foundation**
Every table is isolated by `distributor_id` - each business (distributor) sees only their own data.

### **Authentication Integration**
Uses Supabase Auth with custom user profiles for role-based permissions.

### **AI-First Design**
Every message, order, and product interaction is enhanced with AI processing and learning.

---

## 📊 **Table Categories**

| Category | Tables | Purpose |
|----------|--------|---------|
| **🏢 Multi-Tenancy** | distributors, user_profiles, user_invitations | Business isolation and user management |
| **👥 Customer Management** | customers, customer_labels, customer_label_assignments | Customer data and categorization |
| **💬 Messaging System** | conversations, messages, external_message_mappings | Multi-channel communication |
| **📦 Order Management** | orders, order_products, order_attachments | Order processing and fulfillment |
| **🛍️ Product Catalog** | products, product_categories, product_variants, product_bundles | Product management and AI matching |
| **🤖 AI System** | ai_responses, ai_usage_metrics, ai_errors, ai_training_data | AI processing and optimization |
| **🔐 Security & Privacy** | data_access_audit, pii_detection_results, encryption_keys | Compliance and data protection |
| **🔗 Integrations** | webhook_endpoints, webhook_deliveries, external_integrations | External system connections |

---

## 🏢 **Multi-Tenancy & Authentication**

### **distributors**
**Purpose**: The main tenant table - each row represents a business using the platform.

**Key Fields**:
- `subscription_tier`: FREE, BASIC, PREMIUM, ENTERPRISE
- `ai_confidence_threshold`: Minimum confidence for auto-processing orders
- `monthly_ai_budget_usd`: Cost control for AI usage

**Relationships**:
- ➡️ **customers**: One distributor has many customers
- ➡️ **user_profiles**: One distributor has many users
- ➡️ **orders**: One distributor has many orders

**Why It Exists**: Enables the platform to serve multiple businesses while keeping their data completely isolated.

---

### **user_profiles**
**Purpose**: Links Supabase Auth users to distributors with role-based permissions.

**Key Fields**:
- `id`: References `auth.users(id)` from Supabase Auth
- `role`: OWNER, ADMIN, MANAGER, OPERATOR
- `permissions`: Custom permissions beyond role defaults
- `onboarding_completed`: Track user setup progress

**Relationships**:
- ⬅️ **auth.users**: Each profile links to a Supabase Auth user
- ⬅️ **distributors**: Each user belongs to one distributor
- ➡️ **user_sessions**: User can have multiple active sessions

**Why It Exists**: Bridges Supabase's built-in authentication with our business logic and multi-tenant structure.

---

### **user_invitations**
**Purpose**: Manages team member invitations with role assignment.

**Key Fields**:
- `invitation_token`: Unique token for secure invitation links
- `role`: Role to assign when invitation is accepted
- `expires_at`: 7-day expiry for security

**Relationships**:
- ⬅️ **distributors**: Invitations belong to a distributor
- ⬅️ **user_profiles**: Invited by a specific user

**Why It Exists**: Allows distributed team management where owners/admins can invite team members with specific roles.

---

## 👥 **Customer Management**

### **customers**
**Purpose**: Stores business customers (not end users - this is B2B).

**Key Fields**:
- `business_name`: The customer's business name
- `customer_code`: Unique identifier for the business
- `status`: ORDERING, AT_RISK, STOPPED_ORDERING, NO_ORDERS_YET
- `total_orders`, `total_spent`: Auto-calculated via triggers

**Relationships**:
- ⬅️ **distributors**: Each customer belongs to one distributor
- ➡️ **orders**: Customer can place many orders
- ➡️ **conversations**: Customer can have conversations across channels
- ➡️ **customer_label_assignments**: Customer can have multiple labels

**Why It Exists**: Central repository for business customers with automated status tracking based on ordering behavior.

---

### **customer_labels**
**Purpose**: Categorization system for customers (Dairy, Restaurant, Bar, etc.).

**Key Fields**:
- `name`: Label name (e.g., "Dairy", "Restaurant")
- `color`: Hex color for UI display
- `is_predefined`: System vs custom labels

**Relationships**:
- ⬅️ **distributors**: Labels can be distributor-specific or global
- ➡️ **customer_label_assignments**: Labels applied to customers

**Why It Exists**: Enables flexible customer categorization for filtering, reporting, and targeted marketing.

---

### **customer_label_assignments**
**Purpose**: Many-to-many relationship between customers and labels.

**Key Fields**:
- `value`: Optional additional value for the label

**Relationships**:
- ⬅️ **customers**: Which customer has the label
- ⬅️ **customer_labels**: Which label is assigned

**Why It Exists**: Allows customers to have multiple labels (e.g., a business can be both "Dairy" and "Restaurant").

---

## 💬 **Messaging System**

### **conversations**
**Purpose**: Groups messages by customer and communication channel.

**Key Fields**:
- `channel`: WHATSAPP, SMS, EMAIL
- `unread_count`: Messages from customer not yet read
- `ai_context_summary`: AI-generated conversation summary

**Relationships**:
- ⬅️ **customers**: Each conversation belongs to one customer
- ⬅️ **distributors**: Each conversation belongs to one distributor
- ➡️ **messages**: Conversation contains many messages
- ➡️ **orders**: Orders can be linked to conversations

**Why It Exists**: Organizes messages by customer and channel, enabling unified inbox experience across WhatsApp, SMS, and email.

---

### **messages**
**Purpose**: Individual messages in conversations with AI processing metadata.

**Key Fields**:
- `content`: The actual message text
- `is_from_customer`: Direction of the message
- `ai_processed`: Whether AI has analyzed this message
- `ai_extracted_intent`: AI-detected intent (order, question, complaint)
- `ai_suggested_responses`: AI-generated response suggestions

**Relationships**:
- ⬅️ **conversations**: Each message belongs to one conversation
- ➡️ **ai_responses**: AI can generate multiple responses per message
- ➡️ **orders**: Message can trigger order creation

**Why It Exists**: Core message storage with AI enhancement for intelligent processing and response generation.

---

## 📦 **Order Management**

### **orders**
**Purpose**: Customer orders with AI generation tracking.

**Key Fields**:
- `channel`: Which channel the order came from
- `status`: CONFIRMED, PENDING, REVIEW
- `ai_generated`: Whether order was created by AI from a message
- `ai_confidence`: Confidence level of AI order extraction
- `requires_review`: Whether order needs manual review

**Relationships**:
- ⬅️ **customers**: Each order belongs to one customer
- ⬅️ **conversations**: Orders can be linked to conversations
- ⬅️ **distributors**: Each order belongs to one distributor
- ➡️ **order_products**: Order contains multiple product lines
- ➡️ **order_attachments**: Order can have file attachments

**Why It Exists**: Central order processing with AI integration for automatic order creation from natural language messages.

---

### **order_products**
**Purpose**: Individual line items within orders.

**Key Fields**:
- `product_name`: Text description (future: link to products table)
- `quantity`, `unit_price`, `line_price`: Pricing information
- `ai_extracted`: Whether this line was extracted by AI
- `ai_original_text`: Original message text AI interpreted

**Relationships**:
- ⬅️ **orders**: Each line item belongs to one order
- ➡️ **products**: Future link to product catalog

**Why It Exists**: Detailed order composition with AI extraction tracking for continuous learning and accuracy improvement.

---

## 🛍️ **Product Catalog**

### **products**
**Purpose**: Master product catalog with AI matching capabilities.

**Key Fields**:
- `aliases`: Alternative names customers use
- `keywords`: Search keywords for AI matching
- `ai_training_examples`: Example phrases customers use

**Relationships**:
- ⬅️ **distributors**: Each product belongs to one distributor
- ⬅️ **product_categories**: Products can be categorized
- ➡️ **product_variants**: Products can have variants
- ➡️ **order_products**: Future link from order lines

**Why It Exists**: Enables AI agents to match customer messages to actual products, improving order accuracy and automation.

---

### **product_categories**
**Purpose**: Hierarchical product organization.

**Key Fields**:
- `parent_category_id`: Self-referencing for hierarchy
- `ai_keywords`: Keywords for AI classification

**Relationships**:
- ⬅️ **distributors**: Categories belong to distributors
- ➡️ **products**: Categories contain products
- ➡️ **product_categories**: Self-referencing for subcategories

**Why It Exists**: Organized product structure that helps AI agents understand product relationships and context.

---

### **product_variants**
**Purpose**: Product variations (sizes, colors, etc.).

**Key Fields**:
- `variant_type`: SIZE, COLOR, VOLUME, WEIGHT
- `ai_aliases`: Alternative names for AI matching

**Relationships**:
- ⬅️ **products**: Each variant belongs to one product
- ⬅️ **distributors**: Each variant belongs to one distributor

**Why It Exists**: Handles product complexity while maintaining AI's ability to understand customer requests for specific variants.

---

## 🤖 **AI System**

### **ai_responses**
**Purpose**: Tracks all AI-generated responses for learning and improvement.

**Key Fields**:
- `agent_type`: ORDER_PROCESSING, CUSTOMER_SUPPORT, MESSAGE_ANALYSIS
- `confidence`: AI confidence in the response
- `human_feedback`: User rating of AI response quality
- `tokens_used`: OpenAI API cost tracking

**Relationships**:
- ⬅️ **messages**: AI responses are linked to messages
- ➡️ **ai_training_data**: Poor responses become training data

**Why It Exists**: Continuous AI improvement through response tracking, feedback collection, and cost monitoring.

---

### **ai_usage_metrics**
**Purpose**: Detailed AI usage tracking with hourly granularity.

**Key Fields**:
- `date`, `hour`: Time-based tracking
- `requests_count`: Number of AI requests
- `cost_cents`: Cost in USD cents for precision
- `avg_confidence`: Quality metrics

**Relationships**:
- ⬅️ **distributors**: Usage tracked per distributor

**Why It Exists**: Cost control, performance monitoring, and usage analytics for AI features.

---

### **ai_training_data**
**Purpose**: Collects data for improving AI performance.

**Key Fields**:
- `input_text`: Original message or query
- `expected_output`: What AI should have generated
- `data_source`: MANUAL_ENTRY, CORRECTED_AI_OUTPUT

**Relationships**:
- ⬅️ **distributors**: Training data belongs to distributors

**Why It Exists**: Enables continuous AI improvement through feedback loops and corrected examples.

---

## 🔐 **Security & Privacy**

### **data_access_audit**
**Purpose**: Comprehensive audit trail for data access (GDPR compliance).

**Key Fields**:
- `user_id`: Who accessed the data
- `table_name`, `record_id`: What was accessed
- `operation`: SELECT, INSERT, UPDATE, DELETE
- `contains_pii`: Whether PII was involved

**Relationships**:
- ⬅️ **distributors**: Audit events belong to distributors

**Why It Exists**: Legal compliance (GDPR, HIPAA) and security monitoring for sensitive data access.

---

### **pii_detection_results**
**Purpose**: Tracks personally identifiable information detected in messages.

**Key Fields**:
- `pii_type`: EMAIL, PHONE, ADDRESS, SSN, CREDIT_CARD
- `confidence_score`: Detection confidence
- `reviewed`: Whether human has reviewed the detection

**Relationships**:
- ⬅️ **distributors**: PII detection per distributor
- ⬅️ **pii_detection_rules**: Which rule triggered detection

**Why It Exists**: Automated PII detection for privacy compliance and data protection.

---

## 🔗 **Integrations**

### **webhook_endpoints**
**Purpose**: Configuration for external system webhooks.

**Key Fields**:
- `url`: Webhook destination
- `events`: Array of events to subscribe to
- `auth_type`: Authentication method
- `retry_attempts`: Failure handling

**Relationships**:
- ⬅️ **distributors**: Webhooks belong to distributors
- ➡️ **webhook_deliveries**: Webhooks generate deliveries

**Why It Exists**: Enables real-time integration with WhatsApp Business API, SMS providers, and other external systems.

---

### **webhook_deliveries**
**Purpose**: Tracks webhook delivery attempts and status.

**Key Fields**:
- `event_type`: message.created, order.created, etc.
- `status`: PENDING, SUCCESS, FAILED, RETRYING
- `response_status_code`: HTTP response from webhook

**Relationships**:
- ⬅️ **webhook_endpoints**: Deliveries belong to endpoints
- ⬅️ **messages**, **orders**, **customers**: Event data sources

**Why It Exists**: Reliable webhook delivery with retry logic and debugging information.

---

### **external_integrations**
**Purpose**: Configuration for external service integrations.

**Key Fields**:
- `integration_type`: MESSAGING, ECOMMERCE, CRM, ANALYTICS
- `provider`: Meta, Twilio, SendGrid, etc.
- `config`: Provider-specific settings

**Relationships**:
- ⬅️ **distributors**: Integrations belong to distributors
- ➡️ **external_message_mappings**: Message synchronization

**Why It Exists**: Centralized management of external service connections with provider-specific configurations.

---

## 🔄 **Key Relationships & Data Flow**

### **Message Processing Flow**
```
📱 Customer sends WhatsApp message
    ↓
💬 Message stored in `messages` table
    ↓
🤖 AI analyzes message (`ai_responses`)
    ↓
📦 AI creates order (`orders` + `order_products`)
    ↓
👀 Human reviews if confidence < threshold
    ↓
✅ Order confirmed and processed
```

### **User Authentication Flow**
```
🔐 User signs up with Supabase Auth
    ↓
👤 Profile created in `user_profiles`
    ↓
🏢 User linked to `distributor`
    ↓
🔒 RLS policies enforce data isolation
    ↓
📊 User sees only their distributor's data
```

### **AI Learning Flow**
```
🤖 AI processes message
    ↓
📊 Response tracked in `ai_responses`
    ↓
👍 Human provides feedback
    ↓
📚 Good examples → `ai_training_data`
    ↓
🎯 Future AI responses improve
```

---

## 💡 **Key Design Principles**

### **1. Multi-Tenancy First**
Every table has `distributor_id` for complete data isolation between businesses.

### **2. AI Enhancement**
Every user interaction is captured and enhanced with AI metadata for continuous learning.

### **3. Audit Everything**
All data access and modifications are logged for compliance and debugging.

### **4. Real-time Capable**
Architecture supports real-time updates through triggers and webhooks.

### **5. Extensible Integration**
External systems can be added without changing core schema.

---

## 🚀 **Getting Started for Engineers**

### **Understanding Data Isolation**
1. **Always filter by `distributor_id`** in queries
2. **Use RLS policies** - they automatically enforce tenant isolation
3. **Never hard-code distributor IDs** - use `get_current_distributor_id()`

### **Working with AI Data**
1. **Messages are processed asynchronously** by AI agents
2. **Check `ai_processed` flag** before assuming AI data exists
3. **Always include confidence scores** for AI-generated content

### **Adding New Features**
1. **Add `distributor_id` column** to new tables
2. **Create RLS policies** for tenant isolation
3. **Add AI enhancement fields** if applicable
4. **Update audit triggers** for new sensitive data

---

## 📈 **Performance Considerations**

### **Indexes**
- All foreign keys are indexed
- `distributor_id` is included in composite indexes
- GIN indexes for JSONB and full-text search

### **Query Patterns**
- Queries are optimized for tenant-specific access
- AI processing happens in background jobs
- Real-time features use efficient partial indexes

### **Scaling**
- Schema supports horizontal sharding by distributor
- AI workloads can be processed separately
- Webhook deliveries are queue-based

---

## 🎯 **Common Use Cases**

### **For Frontend Developers**
```sql
-- Get customer conversations with unread counts
SELECT c.*, conv.unread_count 
FROM customers c
JOIN conversations conv ON conv.customer_id = c.id
WHERE c.distributor_id = get_current_distributor_id()
ORDER BY conv.last_message_at DESC;
```

### **For AI Engineers**
```sql
-- Get messages needing AI processing
SELECT * FROM messages 
WHERE ai_processed = FALSE 
AND distributor_id = get_current_distributor_id()
ORDER BY created_at ASC;
```

### **For Analytics**
```sql
-- Monthly AI usage and costs
SELECT date_trunc('month', date) as month,
       SUM(cost_cents)/100.0 as cost_usd,
       SUM(requests_count) as requests
FROM ai_usage_metrics 
WHERE distributor_id = get_current_distributor_id()
GROUP BY month ORDER BY month;
```

This database schema provides a robust foundation for an AI-powered, multi-tenant order management platform with enterprise-grade security and real-time capabilities. 🚀