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
| **🎯 Order Sessions** | conversation_order_sessions, order_session_items, order_session_events | Order collection state management |
| **🛍️ Product Catalog** | products, product_categories, product_variants, product_bundles | Product management and AI matching |
| **🤖 AI System** | ai_responses, ai_usage_metrics, ai_errors, ai_training_data | AI processing and optimization |
| **🔐 Security & Privacy** | data_access_audit, pii_detection_results, encryption_keys | Compliance and data protection |
| **🔗 Integrations** | webhook_endpoints, webhook_deliveries, external_integrations | External system connections |

---

## 🏢 **Multi-Tenancy & Authentication**

### **distributors**
**Purpose**: The main tenant table - each row represents a business using the platform. This is the core table that enables multi-tenancy by isolating all data by business.

**Key Fields** (Complete Column List):
- `id`: Unique identifier for the distributor
- `business_name`: The company's legal or operating name
- `domain`: Custom domain for the distributor (optional)
- `subdomain`: Unique subdomain like "acme.orderagent.com"
- `api_key_hash`: Encrypted API key for external integrations
- `webhook_secret`: Secret for webhook authentication
- `subscription_tier`: FREE, BASIC, PREMIUM, ENTERPRISE - determines feature access
- `subscription_status`: ACTIVE, SUSPENDED, CANCELLED - billing status
- `billing_email`: Email for invoices and billing notifications
- `contact_name`: Primary contact person's name
- `contact_email`: Primary business email for support
- `contact_phone`: Business phone number
- `address`: Physical business address
- `timezone`: Business timezone (default: UTC)
- `locale`: Language preference (default: en)
- `currency`: Business currency (default: USD)
- `ai_enabled`: Whether AI features are active
- `ai_model_preference`: Preferred AI model (default: gpt-4)
- `ai_confidence_threshold`: Minimum confidence (0.0-1.0) for auto-processing orders
- `monthly_ai_budget_usd`: Maximum monthly AI spending limit
- `status`: ACTIVE, INACTIVE, PENDING_SETUP - account status
- `onboarding_completed`: Whether initial setup is finished
- `max_customers`: Customer limit based on subscription
- `max_monthly_messages`: Message limit per month
- `max_monthly_ai_requests`: AI request limit per month
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ➡️ **customers**: One distributor can have many customers (filtered by distributor_id)
- ➡️ **user_profiles**: One distributor can have many team members
- ➡️ **orders**: One distributor processes many orders
- ➡️ **products**: One distributor manages their own product catalog
- ➡️ **conversations**: All conversations belong to one distributor
- ➡️ **ai_usage_metrics**: Tracks AI usage per distributor

**How It Works**: Every major table in the system includes a `distributor_id` column that references this table. This creates complete data isolation - when User A from Company X logs in, they only see data where `distributor_id` matches Company X's ID. This is enforced through Row Level Security (RLS) policies.

**Why It Exists**: Enables Software-as-a-Service (SaaS) multi-tenancy where thousands of businesses can use the same platform while their data remains completely separate and secure.

---

### **user_profiles**
**Purpose**: Links Supabase Auth users to distributors with role-based permissions. This table extends Supabase's authentication with business-specific user data and roles.

**Key Fields** (Complete Column List):
- `id`: Primary key that also references `auth.users(id)` from Supabase Auth
- `distributor_id`: Which business this user belongs to
- `first_name`: User's first name
- `last_name`: User's last name  
- `display_name`: Preferred display name in the UI
- `avatar_url`: Profile picture URL
- `role`: OWNER, ADMIN, MANAGER, OPERATOR - determines base permissions
- `permissions`: Custom permissions beyond role defaults (JSON array)
- `status`: ACTIVE, INACTIVE, SUSPENDED, PENDING - account status
- `email_verified`: Whether user's email is confirmed
- `last_sign_in_at`: Last successful login timestamp
- `last_activity_at`: Last time user performed any action
- `sign_in_count`: Total number of logins
- `timezone`: User's preferred timezone
- `locale`: User's language preference
- `notification_preferences`: Email/SMS notification settings (JSON)
- `onboarding_completed`: Whether user finished initial setup
- `onboarding_step`: Current step in onboarding process
- `require_password_change`: Force password reset on next login
- `two_factor_enabled`: Whether 2FA is active
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **auth.users**: Each profile extends a Supabase Auth user record
- ⬅️ **distributors**: Each user belongs to exactly one distributor (business)
- ➡️ **user_sessions**: User can have multiple active login sessions
- ➡️ **user_invitations**: Users can invite other team members
- ➡️ **ai_responses**: AI responses can be linked to specific users for feedback

**How It Works**: When a user signs up through Supabase Auth, a corresponding record is created here that links them to a specific distributor and assigns them a role. The role determines what data they can access and what actions they can perform within their distributor's data.

**Why It Exists**: Supabase Auth handles authentication (login/logout/passwords) but doesn't know about our business concepts like distributors and roles. This table bridges that gap by connecting authenticated users to business contexts.

---

### **user_invitations**
**Purpose**: Manages team member invitations with role assignment. Enables secure onboarding of new team members to a distributor's account.

**Key Fields** (Complete Column List):
- `id`: Unique invitation identifier
- `distributor_id`: Which business the invitation is for
- `email`: Email address of the person being invited
- `role`: ADMIN, MANAGER, OPERATOR - role to assign when accepted
- `permissions`: Additional permissions beyond the base role (JSON array)
- `invited_by`: User ID of who sent the invitation
- `invitation_token`: Unique secure token for the invitation link
- `status`: PENDING, ACCEPTED, EXPIRED, REVOKED - invitation state
- `expires_at`: When invitation expires (typically 7 days)
- `sent_count`: How many times invitation email was sent
- `last_sent_at`: When invitation was last emailed
- `accepted_at`: When invitation was accepted (if applicable)
- `revoked_at`: When invitation was cancelled (if applicable)
- `revoked_by`: User who cancelled the invitation
- `personal_message`: Custom message from inviter to invitee
- `created_at`: When invitation was created

**Relationships**:
- ⬅️ **distributors**: Each invitation belongs to one distributor
- ⬅️ **user_profiles** (invited_by): Who sent the invitation
- ⬅️ **user_profiles** (revoked_by): Who cancelled the invitation
- ➡️ **user_profiles**: When accepted, creates a new user profile

**How It Works**: When a user with appropriate permissions invites someone, this table stores the invitation with a secure token. An email is sent with a link containing the token. When clicked, the system verifies the token hasn't expired and creates a new user account with the specified role and distributor access.

**Why It Exists**: Enables secure, controlled team growth where business owners can invite employees, contractors, or partners with specific access levels without sharing passwords or manually creating accounts.

---

## 👥 **Customer Management**

### **customers**
**Purpose**: Stores business customers (not end users - this is B2B). Each customer represents a business that orders from the distributor.

**Key Fields** (Complete Column List):
- `id`: Unique customer identifier
- `distributor_id`: Which distributor this customer belongs to
- `business_name`: The customer's business name (e.g., "Mario's Pizza")
- `contact_person_name`: Primary contact at the customer business
- `customer_code`: Unique business identifier (like "MARIO001")
- `email`: Primary business email for orders and communication
- `phone`: Business phone number
- `address`: Physical business address for deliveries
- `avatar_url`: Customer business logo or profile picture
- `status`: ORDERING, AT_RISK, STOPPED_ORDERING, NO_ORDERS_YET - behavior-based status
- `invitation_status`: ACTIVE, PENDING - whether they've accepted platform access
- `joined_date`: When customer first registered
- `last_ordered_date`: Most recent order date (auto-updated)
- `expected_order_date`: When they typically reorder (AI prediction)
- `total_orders`: Total number of orders placed (auto-calculated)
- `total_spent`: Total amount spent across all orders (auto-calculated)
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **distributors**: Each customer belongs to exactly one distributor
- ➡️ **orders**: Customer can place many orders over time
- ➡️ **conversations**: Customer can have conversations across WhatsApp, SMS, email
- ➡️ **customer_label_assignments**: Customer can have multiple category labels
- ➡️ **messages**: Customer receives and sends messages

**How It Works**: When a distributor adds a new business customer, a record is created here. The system automatically updates `total_orders`, `total_spent`, and `last_ordered_date` whenever new orders are placed. The `status` field is automatically updated based on ordering patterns - customers become "AT_RISK" if they haven't ordered recently, or "STOPPED_ORDERING" if they've been inactive for too long.

**Why It Exists**: Provides a complete profile of each business customer including contact information, ordering history, and behavioral status to help distributors manage relationships and identify at-risk accounts.

---

### **customer_labels**
**Purpose**: Categorization system for customers (Dairy, Restaurant, Bar, etc.). Allows distributors to organize customers into business categories.

**Key Fields** (Complete Column List):
- `id`: Unique label identifier
- `distributor_id`: Which distributor owns this label
- `name`: Label name (e.g., "Dairy", "Restaurant", "Bar")
- `color`: Hex color code for UI display (e.g., "#FF5733")
- `description`: Optional detailed description of the label
- `is_predefined`: TRUE for system-provided labels, FALSE for custom ones
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **distributors**: Each label belongs to one distributor (or system-wide if predefined)
- ➡️ **customer_label_assignments**: Many customers can have this label

**How It Works**: Distributors can create custom labels to categorize their customers by business type, size, or other criteria. The system comes with predefined labels like "Restaurant", "Dairy", "Convenience Store" that all distributors can use.

**Why It Exists**: Enables flexible customer segmentation for targeted marketing, reporting, and filtering - helping distributors understand their customer base composition and tailor their approach.

---

### **customer_label_assignments**
**Purpose**: Many-to-many relationship between customers and labels. Enables customers to have multiple category labels.

**Key Fields** (Complete Column List):
- `customer_id`: Which customer this assignment belongs to
- `label_id`: Which label is being assigned
- `value`: Optional additional value for the label (e.g., "Large" for a "Restaurant" label)
- `assigned_at`: When this label was assigned to the customer

**Relationships**:
- ⬅️ **customers**: Which specific customer has this label
- ⬅️ **customer_labels**: Which specific label is assigned

**How It Works**: When a customer needs multiple categories, separate records are created here. For example, a business might be both "Restaurant" and "Dairy" if they serve food and sell milk products. The `value` field allows for additional context like "Large Restaurant" or "Specialty Dairy".

**Why It Exists**: Real businesses often fit multiple categories, so this junction table allows flexible, multi-dimensional customer categorization rather than forcing each customer into a single category.

---

## 💬 **Messaging System**

### **conversations**
**Purpose**: Groups messages by customer and communication channel. Each conversation represents a communication thread between a distributor and customer on a specific channel.

**Key Fields** (Complete Column List):
- `id`: Unique conversation identifier
- `customer_id`: Which customer this conversation is with
- `distributor_id`: Which distributor owns this conversation
- `channel`: WHATSAPP, SMS, EMAIL - the communication method
- `status`: ACTIVE, ARCHIVED - whether conversation is ongoing
- `last_message_at`: Timestamp of most recent message
- `unread_count`: Number of customer messages not yet read by distributor
- `ai_context_summary`: AI-generated summary of conversation topics and status
- `ai_last_processed_at`: When AI last analyzed this conversation
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **customers**: Each conversation belongs to exactly one customer
- ⬅️ **distributors**: Each conversation belongs to exactly one distributor
- ➡️ **messages**: Conversation contains many individual messages
- ➡️ **orders**: Orders can be linked to the conversation where they originated

**How It Works**: When a customer sends their first message via any channel (WhatsApp, SMS, email), a conversation record is created. All subsequent messages between that customer and distributor on that channel are grouped under this conversation. Each customer can have separate conversations per channel (one WhatsApp conversation, one SMS conversation, etc.).

**Why It Exists**: Provides a unified inbox experience where distributors can manage all customer communications across multiple channels in one place, with proper threading and context preservation.

---

### **messages**
**Purpose**: Individual messages in conversations with AI processing metadata. Stores every message sent or received with full AI analysis.

**Key Fields** (Complete Column List):
- `id`: Unique message identifier
- `conversation_id`: Which conversation this message belongs to
- `content`: The actual message text or content
- `is_from_customer`: TRUE if customer sent it, FALSE if distributor sent it
- `message_type`: TEXT, IMAGE, AUDIO, FILE, ORDER_CONTEXT - what kind of message
- `status`: SENT, DELIVERED, READ - delivery status
- `attachments`: JSON array of file attachments (images, PDFs, etc.)
- `ai_processed`: Whether AI has analyzed this message
- `ai_confidence`: AI's confidence level in its analysis (0.0-1.0)
- `ai_extracted_intent`: AI-detected intent (order, question, complaint, greeting)
- `ai_extracted_products`: JSON array of products AI identified in the message
- `ai_suggested_responses`: JSON array of AI-generated response suggestions
- `order_context_id`: Soft reference to order if message created/relates to an order
- `order_session_id`: Links message to an order collection session for grouping related order messages
- `thread_position`: Message sequence number in conversation
- `reply_to_message_id`: If replying to specific message, references that message
- `external_message_id`: ID from external system (WhatsApp, SMS provider)
- `external_metadata`: Additional data from external messaging platform
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **conversations**: Each message belongs to exactly one conversation
- ⬅️ **conversation_order_sessions**: Message can be part of an order collection session
- ➡️ **ai_responses**: AI can generate multiple analysis responses per message
- ➡️ **orders**: Message can trigger automatic order creation
- ⬅️ **messages** (reply_to): Messages can reference other messages in thread

**How It Works**: Every message sent or received is stored here with its full content and metadata. AI automatically processes each message to extract intent, identify products, and suggest responses. The system tracks delivery status and maintains proper threading for complex conversations.

**Why It Exists**: Central repository for all communications with AI enhancement, enabling intelligent automation, order processing, and customer service while maintaining complete message history.

---

## 📦 **Order Management**

### **orders**
**Purpose**: Customer orders with AI generation tracking. Represents a complete order placed by a customer, whether manually entered or AI-generated from messages.

**Key Fields** (Complete Column List):
- `id`: Unique order identifier
- `customer_id`: Which customer placed this order
- `distributor_id`: Which distributor processes this order
- `conversation_id`: Which conversation (if any) this order originated from
- `channel`: WHATSAPP, SMS, EMAIL - how the order was received
- `status`: CONFIRMED, PENDING, REVIEW - current order state
- `received_date`: Date the order was placed
- `received_time`: Time the order was placed
- `delivery_date`: When customer wants delivery (optional)
- `postal_code`: Delivery postal code
- `delivery_address`: Full delivery address
- `total_amount`: Total order value in distributor's currency
- `additional_comment`: Customer notes or special instructions
- `whatsapp_message`: Original WhatsApp message if order came via WhatsApp
- `ai_generated`: TRUE if AI created this order from a message
- `ai_confidence`: AI's confidence level in order extraction (0.0-1.0)
- `ai_source_message_id`: Which message AI used to create this order
- `order_session_id`: Links order to the session that created it
- `is_consolidated`: TRUE if this is the final consolidated order from a session
- `requires_review`: TRUE if order needs human review before processing
- `reviewed_by`: User who reviewed the order (if applicable)
- `reviewed_at`: When the order was reviewed
- `external_order_id`: Reference to order in external system
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **customers**: Each order belongs to exactly one customer
- ⬅️ **conversations**: Orders can be linked to the conversation where they originated
- ⬅️ **conversation_order_sessions**: Orders can be created from an order collection session
- ⬅️ **distributors**: Each order belongs to exactly one distributor
- ➡️ **order_products**: Order contains multiple product line items
- ➡️ **order_attachments**: Order can have file attachments (photos, documents)
- ⬅️ **messages**: AI can reference the source message that created the order

**How It Works**: Orders can be created manually by distributor staff or automatically by AI when it detects ordering intent in customer messages. AI-generated orders are marked with confidence scores and may require human review if confidence is below the distributor's threshold. The system tracks the complete order lifecycle from creation to fulfillment.

**Why It Exists**: Central order management that bridges traditional order entry with AI-powered automation, enabling distributors to process orders from natural language messages while maintaining control and accuracy.

---

### **order_products**
**Purpose**: Individual line items within orders. Each row represents one product type and quantity in an order.

**Key Fields** (Complete Column List):
- `id`: Unique line item identifier
- `order_id`: Which order this line item belongs to
- `product_name`: Text description of the product (e.g., "Whole Milk 1L")
- `product_unit`: Unit of measurement (e.g., "bottles", "cases", "kg")
- `quantity`: How many units ordered
- `unit_price`: Price per unit in distributor's currency
- `line_price`: Total price for this line (quantity × unit_price)
- `ai_extracted`: TRUE if AI extracted this line from a message
- `ai_confidence`: AI's confidence in this line item extraction (0.0-1.0)
- `ai_original_text`: Original message text AI interpreted for this line
- `suggested_product_id`: AI's suggested match to product catalog
- `manual_override`: TRUE if human manually corrected AI extraction
- `line_order`: Position of this line in the order (for display)
- `notes`: Additional notes about this line item
- `matched_product_id`: Actual product from catalog this line refers to
- `matching_confidence`: Confidence in product catalog match (0.0-1.0)
- `matching_method`: EXACT_MATCH, FUZZY_MATCH, AI_MATCH, MANUAL_OVERRIDE
- `matching_score`: Numerical score of catalog match quality
- `alternative_matches`: JSON array of other possible product matches
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **orders**: Each line item belongs to exactly one order
- ⬅️ **products**: Line items can be matched to catalog products
- ⬅️ **product_variants**: Line items can reference specific product variants

**How It Works**: When an order is created (manually or by AI), each product becomes a separate line item here. AI attempts to match line items to the distributor's product catalog using various matching algorithms. The system tracks how confident it is in both the extraction and the catalog matching to enable continuous improvement.

**Why It Exists**: Provides detailed order composition with intelligent product matching, enabling accurate order processing while capturing data to improve AI extraction and product recognition over time.

---

## 🎯 **Order Collection Sessions**

### **conversation_order_sessions**
**Purpose**: Manages order collection sessions within conversations. Implements a state machine for tracking the order lifecycle from initial collection to consolidation.

**Key Fields** (Complete Column List):
- `id`: Unique session identifier
- `conversation_id`: Which conversation this session belongs to
- `distributor_id`: Which distributor owns this session
- `status`: ACTIVE, COLLECTING, REVIEWING, CLOSED - session state machine
- `started_at`: When session was created
- `collecting_started_at`: When actual order collection began
- `review_started_at`: When review phase started
- `closed_at`: When session was closed
- `outcome`: CONFIRMED, CANCELLED, TIMEOUT, ABANDONED - how session ended
- `outcome_reason`: Additional context for the outcome
- `consolidated_order_id`: References final consolidated order
- `session_metadata`: JSON storage for session-specific data
- `ai_confidence_avg`: Average AI confidence across session
- `ai_interactions_count`: Number of AI interactions
- `auto_close_timeout_minutes`: Minutes before auto-closing inactive sessions
- `reminder_sent_at`: When reminder was sent for inactive session
- `created_at`, `updated_at`: Standard timestamps
- `created_by`: User/system that created the session
- `closed_by`: User/system that closed the session

**Relationships**:
- ⬅️ **conversations**: Each session belongs to one conversation
- ⬅️ **distributors**: Each session belongs to one distributor
- ➡️ **messages**: Messages can be linked to a session
- ➡️ **order_session_items**: Session contains collected items
- ➡️ **order_session_events**: Session generates audit events
- ➡️ **orders**: Session creates a consolidated order when confirmed

**How It Works**: When AI detects ordering intent in a conversation, it creates a session to manage the collection process. The session moves through states: ACTIVE (initial) → COLLECTING (gathering items) → REVIEWING (confirming with customer) → CLOSED (completed). Messages and extracted items are linked to the session, providing context and grouping. When confirmed, all items are consolidated into a single order.

**Why It Exists**: Provides structured order collection management, enabling AI to handle complex multi-message order flows while maintaining state, context, and proper customer interaction throughout the ordering process.

---

### **order_session_items**
**Purpose**: Tracks individual items collected during a session before consolidation. Stores products extracted from messages with their status and confidence.

**Key Fields** (Complete Column List):
- `id`: Unique item identifier
- `order_session_id`: Which session this item belongs to
- `product_id`: Reference to product catalog (optional)
- `product_name`: Product name (stored for history)
- `product_code`: Product code for reference
- `quantity`: Number of units requested
- `unit_price`: Price per unit
- `source_message_id`: Which message contained this item
- `ai_extracted`: TRUE if AI extracted this item
- `ai_confidence`: AI's confidence in extraction (0.0-1.0)
- `status`: PENDING, CONFIRMED, REMOVED - item state
- `added_at`: When item was extracted/added
- `confirmed_at`: When customer confirmed item
- `removed_at`: When item was removed
- `item_metadata`: JSON for additional item data

**Relationships**:
- ⬅️ **conversation_order_sessions**: Each item belongs to one session
- ⬅️ **products**: Items can reference catalog products
- ⬅️ **messages**: Items track their source message

**How It Works**: As AI processes messages in a session, it extracts product requests and creates items here. Items start as PENDING and move to CONFIRMED when the customer approves them during review. The system preserves product names and codes even if products are later deleted from the catalog.

**Why It Exists**: Enables granular tracking of order composition during collection, allowing customers to review and modify individual items before final order creation.

---

### **order_session_events**
**Purpose**: Audit trail for all events within an order session. Provides complete visibility into session lifecycle and customer interactions.

**Key Fields** (Complete Column List):
- `id`: Unique event identifier
- `order_session_id`: Which session this event belongs to
- `event_type`: Type of event (SESSION_STARTED, STATUS_CHANGED, ITEM_ADDED, etc.)
- `event_data`: JSON with event-specific details
- `triggered_by`: User/system that triggered the event
- `message_id`: Related message if applicable
- `created_at`: When event occurred

**Event Types**:
- SESSION_STARTED: Session created
- SESSION_CLOSED: Session ended
- STATUS_CHANGED: Session moved to new state
- ITEM_ADDED: Product added to session
- ITEM_REMOVED: Product removed from session
- ITEM_MODIFIED: Quantity/details changed
- REVIEW_REQUESTED: Customer asked to review
- ORDER_CONFIRMED: Customer confirmed order
- ORDER_CANCELLED: Customer cancelled
- REMINDER_SENT: Inactivity reminder sent
- TIMEOUT_WARNING: Session about to timeout
- AI_PROCESSING: AI analyzed message

**Relationships**:
- ⬅️ **conversation_order_sessions**: Each event belongs to one session
- ⬅️ **messages**: Events can reference triggering messages

**How It Works**: Every significant action in a session generates an event record with contextual data. This creates an immutable audit trail for compliance, debugging, and analytics. Events are automatically created by triggers and application code.

**Why It Exists**: Provides complete transparency into order collection process, enabling troubleshooting, compliance auditing, and insights into customer behavior patterns.

---

## 🛍️ **Product Catalog**

### **products**
**Purpose**: Master product catalog with AI matching capabilities. Each product represents an item that the distributor sells.

**Key Fields** (Complete Column List):
- `id`: Unique product identifier
- `distributor_id`: Which distributor owns this product
- `name`: Official product name (e.g., "Organic Whole Milk")
- `sku`: Stock Keeping Unit code (unique product identifier)
- `description`: Detailed product description
- `category`: General category text (deprecated, use category_id)
- `category_id`: Reference to structured product category
- `unit`: Unit of sale ("bottle", "case", "kg", "liter")
- `unit_price`: Standard selling price per unit
- `brand`: Product brand or manufacturer
- `model`: Product model or variant identifier
- `size_variants`: JSON array of available sizes
- `seasonal`: TRUE if product is only available certain times of year
- `minimum_order_quantity`: Smallest quantity that can be ordered
- `maximum_order_quantity`: Largest quantity that can be ordered (optional)
- `lead_time_days`: How many days needed to fulfill order
- `aliases`: JSON array of alternative names customers use
- `keywords`: JSON array of search keywords for AI matching
- `ai_training_examples`: JSON array of example phrases customers use
- `common_misspellings`: JSON array of common misspellings AI should recognize
- `seasonal_patterns`: JSON array of seasonal availability data
- `in_stock`: Whether product is currently available
- `stock_quantity`: Current inventory level (optional)
- `active`: Whether product is currently being sold
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **distributors**: Each product belongs to exactly one distributor
- ⬅️ **product_categories**: Products are organized into categories
- ➡️ **product_variants**: Products can have size/color/type variants
- ➡️ **order_products**: Order lines reference products
- ➡️ **product_bundle_items**: Products can be part of bundles

**How It Works**: Distributors manage their product catalog here, with rich metadata to help AI understand customer requests. When customers mention products in messages, AI uses the aliases, keywords, and training examples to match fuzzy requests like "milk" to "Organic Whole Milk 1L" with high accuracy.

**Why It Exists**: Provides a comprehensive product catalog that enables both human staff and AI agents to accurately identify and process customer product requests, improving order accuracy and automation.

---

### **product_categories**
**Purpose**: Hierarchical product organization. Enables structured categorization of products with nested subcategories.

**Key Fields** (Complete Column List):
- `id`: Unique category identifier
- `distributor_id`: Which distributor owns this category
- `name`: Category name (e.g., "Dairy", "Beverages", "Frozen Foods")
- `parent_category_id`: Self-referencing for hierarchy (NULL for top-level categories)
- `description`: Detailed description of what fits in this category
- `ai_keywords`: JSON array of keywords for AI classification
- `sort_order`: Display order within parent category
- `active`: Whether category is currently in use
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **distributors**: Each category belongs to exactly one distributor
- ➡️ **products**: Categories contain multiple products
- ➡️ **product_categories**: Self-referencing for subcategories (e.g., "Dairy" > "Milk" > "Organic Milk")

**How It Works**: Categories can be nested multiple levels deep (e.g., "Food" > "Dairy" > "Milk" > "Organic"). AI uses category relationships to understand product context and suggest related items. When customers ask for "dairy products", AI can search all products in the dairy category tree.

**Why It Exists**: Provides organized product structure that helps both human users navigate large catalogs and AI agents understand product relationships and context for better matching and suggestions.

---

### **product_variants**
**Purpose**: Product variations (sizes, colors, etc.). Handles different versions of the same base product.

**Key Fields** (Complete Column List):
- `id`: Unique variant identifier
- `product_id`: Which base product this variant belongs to
- `distributor_id`: Which distributor owns this variant
- `variant_name`: Name of this specific variant (e.g., "Large", "500ml", "Red")
- `variant_type`: SIZE, COLOR, VOLUME, WEIGHT, FLAVOR, STYLE
- `sku`: Unique SKU for this specific variant
- `unit_price`: Price for this variant (may differ from base product)
- `price_difference`: Price difference from base product (+/- amount)
- `stock_quantity`: Current inventory for this specific variant
- `low_stock_threshold`: Alert when stock falls below this level
- `ai_aliases`: JSON array of alternative names for AI matching
- `sort_order`: Display order within product variants
- `active`: Whether this variant is currently available
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **products**: Each variant belongs to exactly one base product
- ⬅️ **distributors**: Each variant belongs to exactly one distributor
- ➡️ **order_products**: Order lines can reference specific variants
- ➡️ **product_bundle_items**: Bundles can include specific variants

**How It Works**: When a base product like "Coca Cola" has multiple sizes ("330ml", "500ml", "1L"), each size becomes a variant. AI learns to match customer requests like "large coke" to the "1L" variant of "Coca Cola". Each variant can have its own pricing and inventory tracking.

**Why It Exists**: Handles real-world product complexity where the same item comes in different sizes, colors, or configurations, while maintaining AI's ability to understand and match customer requests for specific variants.

---

## 🤖 **AI System**

### **ai_responses**
**Purpose**: Tracks all AI-generated responses for learning and improvement. Every AI interaction is logged for quality monitoring and cost tracking.

**Key Fields** (Complete Column List):
- `id`: Unique AI response identifier
- `message_id`: Which message triggered this AI response
- `agent_type`: ORDER_PROCESSING, CUSTOMER_SUPPORT, MESSAGE_ANALYSIS, CONTEXT_MANAGER
- `agent_version`: Version of AI agent used (e.g., "v1.0", "v2.3")
- `response_content`: The actual AI-generated response text
- `confidence`: AI's confidence in its response (0.0-1.0)
- `processing_time`: How long AI took to generate response (milliseconds)
- `extracted_data`: JSON of structured data AI extracted (products, intent, etc.)
- `tokens_used`: Number of tokens consumed by OpenAI API
- `model_used`: AI model used (e.g., "gpt-4", "gpt-3.5-turbo")
- `prompt_version`: Version of prompt template used
- `human_feedback`: HELPFUL, PARTIALLY_HELPFUL, NOT_HELPFUL
- `human_feedback_notes`: Detailed feedback from human reviewers
- `was_used`: Whether the AI response was actually used/sent
- `created_at`: When AI generated this response

**Relationships**:
- ⬅️ **messages**: Each AI response is triggered by a specific message
- ➡️ **ai_training_data**: Poor responses become training examples for improvement

**How It Works**: Every time AI processes a message, the response is logged here with metadata about performance, cost, and quality. Human users can rate responses, and this feedback is used to improve future AI performance.

**Why It Exists**: Enables continuous AI improvement through response tracking, human feedback collection, cost monitoring, and performance analysis.

---

### **ai_usage_metrics**
**Purpose**: Detailed AI usage tracking with time-based granularity. Tracks AI consumption for billing and monitoring.

**Key Fields** (Complete Column List):
- `id`: Unique metrics record identifier
- `distributor_id`: Which distributor this usage belongs to
- `period_start`: Start of tracking period (typically hourly)
- `period_end`: End of tracking period
- `requests_count`: Total number of AI requests in this period
- `tokens_used`: Total tokens consumed across all requests
- `cost_usd`: Total cost in USD for this period
- `avg_confidence`: Average confidence score across all AI responses
- `successful_requests`: Number of requests that completed successfully
- `failed_requests`: Number of requests that failed or errored
- `avg_response_time`: Average AI response time in milliseconds
- `peak_concurrent_requests`: Highest number of simultaneous AI requests
- `created_at`: When this metrics record was created

**Relationships**:
- ⬅️ **distributors**: Each metrics record belongs to one distributor

**How It Works**: The system aggregates AI usage data periodically (typically hourly) to track consumption patterns, costs, and performance metrics per distributor. This data is used for billing, monitoring, and optimization.

**Why It Exists**: Provides detailed AI usage analytics for cost control, performance monitoring, billing accuracy, and identifying optimization opportunities.

---

### **ai_training_data**
**Purpose**: Collects data for improving AI performance. Stores examples of correct AI responses for training and fine-tuning.

**Key Fields** (Complete Column List):
- `id`: Unique training data identifier
- `input_text`: Original message or query text
- `input_context`: JSON of additional context (customer history, product catalog, etc.)
- `expected_output`: JSON of what AI should have generated
- `expected_confidence`: What confidence level AI should have had
- `actual_output`: JSON of what AI actually generated (if applicable)
- `actual_confidence`: What confidence level AI actually had
- `data_source`: MANUAL_ENTRY, CORRECTED_AI_OUTPUT, EXPERT_REVIEW
- `quality_score`: Human rating of training example quality (1-5)
- `used_in_training`: Whether this example has been used to train AI models
- `training_batch`: Identifier for which training batch included this example
- `created_at`: When training example was created

**Relationships**:
- ⬅️ **distributors**: Training data can be distributor-specific for customization
- ⬅️ **ai_responses**: Training data can be derived from corrected AI responses

**How It Works**: When AI makes mistakes or when experts want to teach AI new patterns, examples are stored here. These examples are used to fine-tune AI models and improve performance for specific distributors or use cases.

**Why It Exists**: Enables continuous AI improvement through curated training examples, allowing the system to learn from mistakes and expert knowledge to provide better results over time.

---

## 🔐 **Security & Privacy**

### **data_access_audit**
**Purpose**: Comprehensive audit trail for data access (GDPR compliance). Logs every database operation for security and legal compliance.

**Key Fields** (Complete Column List):
- `id`: Unique audit record identifier
- `table_name`: Which database table was accessed
- `operation`: SELECT, INSERT, UPDATE, DELETE - what action was performed
- `user_id`: Which user performed the action (if applicable)
- `distributor_id`: Which distributor the accessed data belongs to
- `attempted_record_id`: ID of the specific record accessed
- `ip_address`: IP address of the user who performed the action
- `user_agent`: Browser/application information
- `created_at`: Exact timestamp of the access

**Relationships**:
- ⬅️ **distributors**: Audit events are associated with distributors
- ⬅️ **user_profiles**: Audit events can be linked to specific users

**How It Works**: Every database operation is automatically logged through database triggers and application-level auditing. This creates an immutable trail of who accessed what data when, essential for GDPR compliance and security investigations.

**Why It Exists**: Provides legal compliance (GDPR, HIPAA), security monitoring for detecting unauthorized access, and forensic capabilities for investigating data breaches or misuse.

---

### **pii_detection_results**
**Purpose**: Tracks personally identifiable information detected in messages. Automatically identifies sensitive data for privacy protection.

**Key Fields** (Complete Column List):
- `id`: Unique PII detection identifier
- `distributor_id`: Which distributor this detection belongs to
- `message_id`: Which message contained the PII (if applicable)
- `field_name`: Which database field contained PII
- `pii_type`: EMAIL, PHONE, ADDRESS, SSN, CREDIT_CARD, NAME, DATE_OF_BIRTH
- `detected_value`: The actual PII value detected (encrypted)
- `confidence_score`: AI confidence in PII detection (0.0-1.0)
- `detection_rule_id`: Which detection rule identified this PII
- `reviewed`: Whether human has reviewed and confirmed the detection
- `is_false_positive`: Whether detection was incorrect
- `reviewed_by`: User who reviewed the detection
- `reviewed_at`: When the detection was reviewed
- `action_taken`: What action was taken (REDACTED, ENCRYPTED, FLAGGED)
- `created_at`: When PII was detected

**Relationships**:
- ⬅️ **distributors**: PII detections are associated with distributors
- ⬅️ **messages**: PII can be detected in message content
- ⬅️ **user_profiles**: Detection reviews are linked to users

**How It Works**: AI automatically scans all message content and form data for patterns that match PII types. When detected, the system can automatically redact, encrypt, or flag the data for review while logging the detection for compliance purposes.

**Why It Exists**: Ensures privacy compliance (GDPR, CCPA) by automatically detecting and protecting personally identifiable information in customer communications and data.

---

## 🔗 **Integrations**

### **webhook_endpoints**
**Purpose**: Configuration for external system webhooks. Defines where and how to send real-time event notifications to external systems.

**Key Fields** (Complete Column List):
- `id`: Unique webhook endpoint identifier
- `distributor_id`: Which distributor owns this webhook
- `name`: Human-readable name for the webhook
- `url`: Destination URL where events will be sent
- `events`: JSON array of event types to subscribe to (e.g., ["message.created", "order.created"])
- `auth_type`: NONE, API_KEY, BEARER_TOKEN, HMAC_SHA256
- `auth_value`: Authentication credential (encrypted)
- `retry_attempts`: Maximum number of retry attempts on failure
- `retry_delay_seconds`: Delay between retry attempts
- `timeout_seconds`: Request timeout before considering delivery failed
- `active`: Whether webhook is currently enabled
- `last_triggered_at`: When webhook was last fired
- `total_deliveries`: Count of all delivery attempts
- `successful_deliveries`: Count of successful deliveries
- `failed_deliveries`: Count of failed deliveries
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **distributors**: Each webhook belongs to exactly one distributor
- ➡️ **webhook_deliveries**: Webhooks generate multiple delivery attempts

**How It Works**: When configured events occur (new message, order created, etc.), the system sends HTTP POST requests to the specified URL with event data. Authentication and retry logic ensure reliable delivery to external systems.

**Why It Exists**: Enables real-time integration with external systems like WhatsApp Business API, SMS providers, CRM systems, and custom applications that need immediate notification of platform events.

---

### **webhook_deliveries**
**Purpose**: Tracks webhook delivery attempts and status. Logs every attempt to deliver webhook events for monitoring and debugging.

**Key Fields** (Complete Column List):
- `id`: Unique delivery attempt identifier
- `webhook_endpoint_id`: Which webhook endpoint this delivery is for
- `event_type`: Specific event type (e.g., "message.created", "order.confirmed")
- `event_data`: JSON payload sent to webhook
- `status`: PENDING, SUCCESS, FAILED, RETRYING
- `attempt_number`: Which retry attempt this is (1 for first attempt)
- `scheduled_at`: When delivery is/was scheduled
- `attempted_at`: When delivery attempt was made
- `completed_at`: When delivery attempt finished
- `response_status_code`: HTTP status code returned by webhook endpoint
- `response_body`: Response body from webhook endpoint
- `response_headers`: Response headers from webhook endpoint
- `error_message`: Error details if delivery failed
- `retry_after`: When next retry attempt is scheduled
- `created_at`: When delivery record was created

**Relationships**:
- ⬅️ **webhook_endpoints**: Each delivery belongs to one webhook endpoint
- ⬅️ **messages**, **orders**, **customers**: Event data sources (soft references through event_data)

**How It Works**: When an event occurs, a delivery record is created with the event data. The system attempts delivery and logs the response. If delivery fails, retry records are created based on the webhook's retry configuration.

**Why It Exists**: Provides reliable webhook delivery with comprehensive logging for monitoring, debugging, and ensuring external systems receive all important events.

---

### **external_integrations**
**Purpose**: Configuration for external service integrations. Manages connections to third-party services like messaging platforms, CRMs, and e-commerce systems.

**Key Fields** (Complete Column List):
- `id`: Unique integration identifier
- `distributor_id`: Which distributor owns this integration
- `integration_type`: MESSAGING, ECOMMERCE, CRM, ANALYTICS, PAYMENT, SHIPPING
- `provider`: Provider name (e.g., "Meta", "Twilio", "SendGrid", "Shopify")
- `provider_version`: API version or integration version
- `display_name`: Human-readable name for this integration
- `config`: JSON of provider-specific configuration settings
- `credentials`: JSON of encrypted authentication credentials
- `webhook_url`: URL for receiving webhooks from this provider
- `webhook_secret`: Secret for validating webhook authenticity
- `status`: ACTIVE, INACTIVE, ERROR, PENDING_AUTH
- `last_sync_at`: When data was last synchronized with provider
- `sync_frequency_minutes`: How often to sync data
- `error_count`: Number of consecutive errors
- `last_error_message`: Details of most recent error
- `capabilities`: JSON array of what this integration can do
- `rate_limit_remaining`: Current API rate limit status
- `rate_limit_reset_at`: When rate limit resets
- `created_at`, `updated_at`: Standard timestamps

**Relationships**:
- ⬅️ **distributors**: Each integration belongs to exactly one distributor
- ➡️ **external_message_mappings**: Maps internal messages to external system IDs
- ➡️ **webhook_deliveries**: Integration events can trigger webhooks

**How It Works**: Distributors configure integrations with external services by providing API credentials and settings. The system uses these configurations to sync data, send messages, and receive webhooks from external platforms.

**Why It Exists**: Provides centralized management of external service connections, enabling seamless integration with messaging platforms (WhatsApp, SMS), e-commerce systems, CRMs, and other business tools.

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

### **Order Session Flow**
```
💬 Customer starts ordering in conversation
    ↓
🎯 Session created in `conversation_order_sessions`
    ↓
📝 AI extracts items → `order_session_items`
    ↓
🔄 Multiple messages add/modify items
    ↓
👀 Customer reviews collected items
    ↓
✅ Session confirmed → Consolidated `order` created
    ↓
📊 All events logged in `order_session_events`
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

### **For Order Sessions**
```sql
-- Get active order sessions with item counts
SELECT s.*, 
       COUNT(DISTINCT i.id) as total_items,
       COALESCE(SUM(i.quantity * i.unit_price), 0) as total_value
FROM conversation_order_sessions s
LEFT JOIN order_session_items i ON i.order_session_id = s.id
WHERE s.status IN ('ACTIVE', 'COLLECTING', 'REVIEWING')
  AND s.distributor_id = get_current_distributor_id()
GROUP BY s.id;
```

This database schema provides a robust foundation for an AI-powered, multi-tenant order management platform with enterprise-grade security and real-time capabilities. 🚀