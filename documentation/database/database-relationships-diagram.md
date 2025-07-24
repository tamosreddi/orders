# 🔗 Database Relationships & Entity Diagram

**Visual guide to table connections and data flow in the AI-powered order management platform**

## 🎯 **Relationship Types Legend**

| Symbol | Meaning | Example |
|--------|---------|---------|
| `1 ──→ ∞` | One-to-Many | One distributor has many customers |
| `∞ ←─→ ∞` | Many-to-Many | Customers can have many labels |
| `1 ──→ 1` | One-to-One | User profile links to one auth user |
| `?──→` | Optional | Order may reference a conversation |

---

## 🏗️ **Core Entity Relationships**

### **Multi-Tenant Foundation**
```
distributors (🏢 Business)
    ├── 1 ──→ ∞ customers
    ├── 1 ──→ ∞ user_profiles  
    ├── 1 ──→ ∞ orders
    ├── 1 ──→ ∞ conversations
    ├── 1 ──→ ∞ products
    ├── 1 ──→ ∞ webhook_endpoints
    └── 1 ──→ ∞ external_integrations
```

### **Customer Management Chain**
```
customers (👤 Business Customer)
    ├── 1 ──→ ∞ orders
    ├── 1 ──→ ∞ conversations  
    └── ∞ ←─→ ∞ customer_labels
            (via customer_label_assignments)
```

### **Messaging & Communication Flow**
```
conversations (💬 Channel Conversation)
    ├── 1 ──→ ∞ messages
    ├── ?──→ ∞ orders (optional link)
    └── 1 ←── 1 customers

messages (📝 Individual Message)
    ├── 1 ──→ ∞ ai_responses
    ├── ?──→ 1 orders (can trigger order)
    └── 1 ←── 1 conversations
```

### **Order Processing Chain**
```
orders (📦 Customer Order)
    ├── 1 ──→ ∞ order_products
    ├── 1 ──→ ∞ order_attachments
    ├── ?──→ 1 conversations (if from message)
    ├── ?──→ 1 messages (source message)
    └── 1 ←── 1 customers

order_products (📋 Line Item)
    ├── ?──→ 1 products (future link)
    └── 1 ←── 1 orders
```

---

## 🤖 **AI System Relationships**

### **AI Processing Flow**
```
messages
    ├── 1 ──→ ∞ ai_responses
    └── triggers AI analysis

ai_responses (🧠 AI Analysis)
    ├── 1 ←── 1 messages
    ├── feeds → ai_training_data
    └── tracked in → ai_usage_metrics

ai_usage_metrics (📊 Usage Tracking)
    ├── aggregates from → ai_responses
    ├── triggers → ai_budget_alerts
    └── 1 ←── 1 distributors
```

### **Product AI Matching**
```
products (🛍️ Catalog Item)
    ├── 1 ──→ ∞ product_variants
    ├── 1 ←── 1 product_categories
    ├── ∞ ←─→ ∞ product_bundles
    └── tracked in → product_matching_history

product_matching_history
    ├── links → order_products
    ├── references → products
    └── improves AI matching
```

---

## 🔐 **Authentication & Security Relationships**

### **User Management**
```
auth.users (Supabase Auth) 🔐
    └── 1 ──→ 1 user_profiles

user_profiles (👤 Platform User)
    ├── 1 ←── 1 distributors
    ├── 1 ──→ ∞ user_sessions
    ├── creates → user_invitations
    └── tracked in → data_access_audit
```

### **Security & Audit Trail**
```
data_access_audit (🔍 Audit Log)
    ├── tracks access to → ALL TABLES
    ├── 1 ←── 1 distributors
    └── 1 ←── ? user_profiles

pii_detection_results (🛡️ Privacy)
    ├── scans → messages
    ├── uses → pii_detection_rules
    └── 1 ←── 1 distributors
```

---

## 🔗 **Integration Relationships**

### **Webhook System**
```
webhook_endpoints (🔌 External URLs)
    ├── 1 ──→ ∞ webhook_deliveries
    └── 1 ←── 1 distributors

webhook_deliveries (📡 Event Delivery)
    ├── triggered by → messages
    ├── triggered by → orders  
    ├── triggered by → customers
    └── 1 ←── 1 webhook_endpoints
```

### **External Integrations**
```
external_integrations (🌐 External Services)
    ├── 1 ──→ ∞ external_message_mappings
    ├── manages → api_rate_limits
    └── 1 ←── 1 distributors

external_message_mappings (🔄 Message Sync)
    ├── maps → messages
    ├── maps → conversations
    └── 1 ←── 1 external_integrations
```

---

## 📊 **Complete Entity Relationship Diagram**

```
🏢 DISTRIBUTORS
├─ 🔐 AUTH & USERS
│  ├─ auth.users ──→ user_profiles
│  ├─ user_profiles ──→ user_sessions
│  ├─ user_profiles ──→ user_invitations
│  └─ role_permissions
│
├─ 👥 CUSTOMERS  
│  ├─ customers
│  ├─ customer_labels ←─→ customer_label_assignments ←─→ customers
│  └─ distributor_usage
│
├─ 💬 MESSAGING
│  ├─ conversations ──→ messages
│  ├─ messages ──→ ai_responses
│  └─ external_message_mappings
│
├─ 📦 ORDERS
│  ├─ orders ──→ order_products
│  ├─ orders ──→ order_attachments  
│  └─ orders ←─? conversations (optional)
│
├─ 🛍️ PRODUCTS
│  ├─ product_categories ──→ products
│  ├─ products ──→ product_variants
│  ├─ product_bundles ←─→ product_bundle_items ←─→ products
│  └─ product_matching_history
│
├─ 🤖 AI SYSTEM
│  ├─ ai_responses
│  ├─ ai_usage_metrics
│  ├─ ai_model_performance
│  ├─ ai_errors
│  ├─ ai_training_data
│  ├─ ai_prompt_performance
│  └─ ai_budget_alerts
│
├─ 🔒 SECURITY
│  ├─ data_access_audit
│  ├─ pii_detection_rules ──→ pii_detection_results
│  ├─ data_retention_policies
│  ├─ encryption_keys
│  └─ security_audit_log
│
└─ 🔗 INTEGRATIONS
   ├─ webhook_endpoints ──→ webhook_deliveries
   ├─ external_integrations ──→ external_message_mappings
   ├─ api_rate_limits
   └─ webhook_event_templates
```

---

## 🌊 **Data Flow Patterns**

### **1. Message-to-Order Flow**
```
📱 WhatsApp Message
    ↓ creates
💬 Message Record
    ↓ triggers
🤖 AI Analysis (ai_responses)
    ↓ may create
📦 Order Record
    ↓ contains
📋 Order Products
    ↓ optionally links to
🛍️ Product Catalog
```

### **2. User Authentication Flow**
```
🔐 Supabase Auth Registration
    ↓ triggers
👤 User Profile Creation
    ↓ checks for
✉️ User Invitation
    ↓ assigns
🏢 Distributor Association
    ↓ enforces
🔒 RLS Data Isolation
```

### **3. AI Learning Flow**
```
📝 User Message
    ↓ processed by
🤖 AI Agent
    ↓ generates
💭 AI Response
    ↓ receives
👍 Human Feedback
    ↓ becomes
📚 Training Data
    ↓ improves
🎯 Future AI Performance
```

### **4. Webhook Integration Flow**
```
📦 Order Created
    ↓ triggers
🔔 Event Generation
    ↓ queues
📡 Webhook Delivery
    ↓ sends to
🌐 External System
    ↓ logs
📊 Delivery Status
```

---

## 🎯 **Critical Relationship Rules**

### **Multi-Tenancy Enforcement**
- **Every data table MUST have `distributor_id`**
- **RLS policies enforce `distributor_id` filtering**
- **Cross-distributor data access is impossible**

### **AI Data Consistency**
- **Messages ➔ AI Responses**: One message can have multiple AI analyses
- **AI Responses ➔ Training Data**: Poor responses become training examples
- **Usage Tracking**: Every AI call increments usage metrics

### **Order Integrity**
- **Orders ➔ Products**: Line items reference products (future enhancement)
- **Conversations ➔ Orders**: Orders can be linked to source conversations
- **Customers ➔ Orders**: Every order must belong to a customer

### **Security & Audit**
- **All sensitive operations logged in `data_access_audit`**
- **PII detection runs on all message content**
- **User sessions tracked for security monitoring**

---

## 🔧 **Foreign Key Constraints**

### **Critical Dependencies**
```sql
-- Multi-tenancy (CASCADE DELETE)
customers.distributor_id → distributors.id
orders.distributor_id → distributors.id
conversations.distributor_id → distributors.id

-- User management (CASCADE DELETE)  
user_profiles.id → auth.users.id
user_profiles.distributor_id → distributors.id

-- Message chain (CASCADE DELETE)
messages.conversation_id → conversations.id
ai_responses.message_id → messages.id

-- Order chain (CASCADE DELETE)
order_products.order_id → orders.id
order_attachments.order_id → orders.id

-- Product hierarchy (CASCADE DELETE)
product_variants.product_id → products.id
product_bundle_items.bundle_id → product_bundles.id
```

### **Optional References (SET NULL)**
```sql
-- Optional links that can be broken
orders.conversation_id → conversations.id (SET NULL)
orders.ai_source_message_id → messages.id (SET NULL)
product_categories.parent_category_id → product_categories.id (SET NULL)
```

---

## 💡 **Understanding the Relationships**

### **For New Engineers**

1. **Start with `distributors`** - every query should be tenant-aware
2. **Follow the customer journey**: Customer → Conversation → Message → AI Response → Order
3. **AI enhances everything**: Most user actions generate AI metadata
4. **Security is layered**: RLS + Audit + PII Detection + Encryption
5. **Integrations are event-driven**: Changes trigger webhooks to external systems

### **Common Query Patterns**

```sql
-- Get customer with recent activity
SELECT c.*, COUNT(o.id) as order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id 
WHERE c.distributor_id = get_current_distributor_id()
GROUP BY c.id;

-- Get conversation with AI-suggested responses
SELECT m.*, ar.response_content
FROM messages m
LEFT JOIN ai_responses ar ON ar.message_id = m.id
WHERE m.conversation_id = $1
ORDER BY m.created_at;

-- Get AI usage and costs
SELECT SUM(cost_cents)/100.0 as total_cost_usd,
       AVG(avg_confidence) as avg_confidence
FROM ai_usage_metrics 
WHERE distributor_id = get_current_distributor_id()
AND date >= date_trunc('month', now());
```

This relationship guide helps engineers understand how data flows through the system and how tables connect to support the AI-powered order management platform. 🚀