# 📚 Database Documentation

**Complete documentation for the AI-powered order management platform database**

## 📖 **Documentation Overview**

This folder contains comprehensive documentation to help engineers understand and work with our database architecture. The documentation is organized for maximum clarity and practical use.

---

## 📁 **Documentation Files**

### **🏗️ [Database Schema Guide](./database-schema-guide.md)**
**Primary reference for all engineers**

- **Complete table descriptions** with purpose and use cases
- **Field explanations** for every important column
- **Why each table exists** and how it fits the business logic
- **Design principles** behind the architecture
- **Performance considerations** and optimization tips

**👥 Target Audience**: All engineers (frontend, backend, AI, DevOps)

---

### **🔗 [Database Relationships Diagram](./database-relationships-diagram.md)**
**Visual guide to table connections**

- **Entity relationship diagrams** showing all table connections
- **Data flow patterns** for key user journeys
- **Foreign key constraints** and referential integrity rules
- **Multi-tenant architecture** visualization
- **Critical relationship rules** and dependencies

**👥 Target Audience**: Backend engineers, database administrators, system architects

---

### **🛠️ [Practical Examples](./practical-examples.md)**
**Real-world code examples and use cases**

- **Complete SQL queries** for common scenarios
- **Frontend integration** patterns and examples
- **AI data processing** examples with confidence handling
- **Performance-optimized** query patterns
- **Multi-tenant filtering** templates and best practices

**👥 Target Audience**: Frontend and backend developers building features

---

## 🚀 **Quick Start Guide**

### **For New Engineers**

1. **Start with**: [Database Schema Guide](./database-schema-guide.md)
   - Understand the overall architecture
   - Learn about multi-tenancy and AI integration
   - Get familiar with core table categories

2. **Then read**: [Database Relationships Diagram](./database-relationships-diagram.md)
   - See how tables connect and relate
   - Understand data flow patterns
   - Learn critical relationship rules

3. **Finally use**: [Practical Examples](./practical-examples.md)
   - Copy-paste working queries
   - Understand common patterns
   - See real implementation examples

### **For Specific Roles**

**🎨 Frontend Developers**
- Focus on: Schema Guide (table purposes) + Practical Examples (queries)
- Key sections: Customer Management, Messaging System, Order Management
- Important: Multi-tenant filtering patterns, AI data handling

**⚙️ Backend Developers** 
- Read all three documents thoroughly
- Pay special attention to: Relationships, Foreign Keys, Performance patterns
- Critical: RLS policies, trigger functions, AI integration patterns

**🤖 AI Engineers**
- Focus on: AI System tables, AI training data flow, AI performance monitoring
- Key sections: AI Response tracking, Usage metrics, Training data collection
- Important: Confidence scoring, cost tracking, feedback loops

**🔒 DevOps/Security Engineers**
- Focus on: Security & Privacy tables, Audit trails, RLS policies
- Key sections: Authentication, Data access audit, PII detection
- Important: Multi-tenant isolation, encryption, compliance features

---

## 🏗️ **Database Architecture Summary**

### **🎯 Core Principles**

1. **Multi-Tenant First**: Every table isolates data by `distributor_id`
2. **AI Enhanced**: All user interactions generate AI metadata for learning
3. **Security by Design**: Comprehensive audit trails and RLS policies
4. **Real-time Ready**: Trigger-based updates and webhook integrations
5. **Extensible**: New features can be added without breaking changes

### **📊 Key Statistics**

- **47 tables** across 8 functional categories
- **15 migration files** with complete schema
- **Row Level Security** on all data tables
- **Multi-channel messaging** (WhatsApp, SMS, Email)
- **AI cost tracking** with budget controls
- **GDPR compliance** with PII detection and audit trails

### **🔧 Technology Stack**

- **Database**: PostgreSQL 15 with Supabase
- **Authentication**: Supabase Auth with custom profiles
- **AI Integration**: OpenAI API with usage tracking
- **Real-time**: Triggers + Webhooks + WebSocket support
- **Security**: RLS + Encryption + Audit trails

---

## 🎯 **Common Use Cases**

### **Building the Messages Page**
```sql
-- Get conversations with AI context
SELECT c.*, conv.unread_count, conv.last_message_at
FROM customers c
JOIN conversations conv ON conv.customer_id = c.id
WHERE c.distributor_id = get_current_distributor_id()
ORDER BY conv.last_message_at DESC;
```

### **AI Order Processing**
```sql
-- Process messages with AI and create orders
SELECT m.*, ar.extracted_data, ar.confidence
FROM messages m
LEFT JOIN ai_responses ar ON ar.message_id = m.id
WHERE m.ai_processed = FALSE
AND m.distributor_id = get_current_distributor_id();
```

### **Customer Analytics**
```sql
-- Customer activity and risk analysis
SELECT c.*, COUNT(o.id) as order_count,
       SUM(o.total_amount) as total_spent
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE c.distributor_id = get_current_distributor_id()
GROUP BY c.id;
```

---

## 🔍 **Finding What You Need**

### **By Feature Area**

| Feature | Primary Tables | Documentation Section |
|---------|---------------|----------------------|
| **Customer Management** | customers, customer_labels | Schema Guide → Customer Management |
| **Messaging & Chat** | conversations, messages, ai_responses | Schema Guide → Messaging System |
| **Order Processing** | orders, order_products | Schema Guide → Order Management |
| **Product Catalog** | products, product_categories | Schema Guide → Product Catalog |
| **AI & Analytics** | ai_usage_metrics, ai_responses | Schema Guide → AI System |
| **User Management** | user_profiles, user_invitations | Schema Guide → Authentication |
| **Integrations** | webhook_endpoints, external_integrations | Schema Guide → Integrations |

### **By Query Type**

| Need | Look In | Example |
|------|---------|---------|
| **Dashboard queries** | Practical Examples → Customer Dashboard | Customer activity summary |
| **AI processing** | Practical Examples → AI Examples | Message analysis, confidence scoring |
| **Real-time updates** | Relationships → Data Flow | Message → AI → Order flow |
| **Security compliance** | Schema Guide → Security | Audit trails, PII detection |
| **Performance optimization** | All docs | Indexes, query patterns, best practices |

---

## 🆘 **Getting Help**

### **Understanding Tables**
1. Check **Schema Guide** for table purpose and fields
2. Look at **Relationships Diagram** for connections
3. Find **Practical Examples** for working queries

### **Building Queries**
1. Start with **multi-tenant filtering** template
2. Use **AI data checking** patterns for AI features  
3. Copy relevant examples from **Practical Examples**
4. Test with small datasets first

### **Performance Issues**
1. Ensure **proper indexes** are being used
2. Check **multi-tenant filtering** is applied
3. Review **query patterns** in documentation
4. Consider **pagination** for large result sets

### **Security Concerns**
1. Verify **RLS policies** are enforced
2. Check **audit logging** is working
3. Ensure **PII detection** is active
4. Review **user permissions** and roles

---

## 🔄 **Keeping Documentation Updated**

### **When to Update**
- **New tables** added to schema
- **New relationships** created between tables
- **New query patterns** become common
- **Performance optimizations** discovered
- **Security policies** changed

### **How to Update**
1. **Schema changes**: Update all three documentation files
2. **New examples**: Add to Practical Examples with context
3. **Relationship changes**: Update the relationships diagram
4. **Performance tips**: Add to relevant sections

---

## 📈 **Database Health Monitoring**

### **Key Metrics to Watch**
- **AI processing costs** and budget usage
- **Query performance** and slow queries
- **RLS policy** enforcement and violations
- **Webhook delivery** success rates
- **Data growth** and storage usage

### **Regular Maintenance**
- **Review AI training data** quality monthly
- **Clean up old audit logs** per retention policy
- **Monitor PII detection** accuracy
- **Update product matching** algorithms
- **Optimize frequently used queries**

---

This documentation provides everything needed to understand, build with, and maintain our AI-powered order management database. 

**Happy coding!** 🚀

---

**📝 Last Updated**: July 2024  
**📖 Version**: 1.0  
**👥 Maintained by**: Engineering Team