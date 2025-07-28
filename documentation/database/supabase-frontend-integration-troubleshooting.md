# Supabase Frontend Integration Troubleshooting Guide

This document covers common issues encountered when connecting frontend components to Supabase tables and their solutions.

## 🎯 Overview

When integrating frontend forms (like InviteCustomerPanel) with Supabase database tables, several common issues can arise related to data types, triggers, webhooks, and field mappings. This guide provides solutions based on real implementation experience.

## 🚨 Common Issues & Solutions

### **Issue 1: Data Type Mismatches**

#### **Problem:**
```
HTTP 400 Bad Request - Field type validation errors
```

#### **Root Cause:**
Frontend sends data types that don't match database schema expectations.

#### **Common Examples:**
1. **Date Fields**: Sending `"2025-07-24"` to a `timestamp with time zone` field
2. **UUID Fields**: Sending string IDs to UUID columns
3. **Null Handling**: Sending `undefined` instead of `null`

#### **Solution:**
```typescript
// ❌ Wrong - sends date string to timestamp field
joined_date: new Date().toISOString().split('T')[0], // "2025-07-24"

// ✅ Correct - sends full ISO timestamp
joined_date: new Date().toISOString(), // "2025-07-24T11:34:10.123Z"

// ❌ Wrong - undefined values
phone: customerData.phone, // might be undefined

// ✅ Correct - explicit null handling
phone: customerData.phone || null,
```

#### **Prevention:**
Always check database schema before mapping data:
```sql
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'your_table' 
ORDER BY ordinal_position;
```

---

### **Issue 2: Database Trigger Errors**

#### **Problem:**
```
CustomerError: Something went wrong. Please try again
Error code: 42703 - "record 'new' has no field 'field_name'"
```

#### **Root Cause:**
Database triggers (webhooks, activity tracking) try to access fields that don't exist on the table being inserted into.

#### **Investigation Steps:**
1. **Check active triggers:**
```sql
SELECT trigger_name, event_manipulation, action_statement 
FROM information_schema.triggers 
WHERE event_object_table = 'your_table';
```

2. **Examine trigger functions:**
```sql
SELECT prosrc FROM pg_proc WHERE proname = 'trigger_function_name';
```

#### **Common Trigger Issues:**
1. **Cross-table field references**: Trigger tries to access `NEW.customer_id` on customers table
2. **Missing field handling**: Trigger assumes fields exist on all tables
3. **Parameter mismatches**: Function calls with wrong parameter types

#### **Solution Pattern:**
```sql
-- Fix trigger function to handle different tables properly
CREATE OR REPLACE FUNCTION auto_trigger_webhooks()
RETURNS TRIGGER AS $$
DECLARE
    event_type_var TEXT;
    event_data_var JSONB;
    dist_id UUID;
BEGIN
    -- Handle each table type specifically
    CASE TG_TABLE_NAME
        WHEN 'customers' THEN
            -- Use customer-specific logic
            dist_id := NEW.distributor_id;
            event_data_var := jsonb_build_object(
                'customer_id', NEW.id,  -- Use NEW.id, not NEW.customer_id
                'business_name', NEW.business_name
            );
        WHEN 'orders' THEN
            -- Use order-specific logic
            dist_id := NEW.distributor_id;
            event_data_var := jsonb_build_object(
                'order_id', NEW.id,
                'customer_id', NEW.customer_id  -- This field exists on orders
            );
    END CASE;
    
    -- Call webhook with proper NULL handling
    PERFORM trigger_webhook_delivery(
        event_type_var,
        event_data_var,
        dist_id,
        CASE WHEN TG_TABLE_NAME = 'customers' THEN NULL::uuid 
             ELSE NEW.conversation_id END,  -- Only messages have conversation_id
        NULL::uuid,  -- Explicit type casting for NULL values
        CASE WHEN TG_TABLE_NAME = 'customers' THEN NEW.id 
             ELSE NEW.customer_id END
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

### **Issue 3: Webhook Function Parameter Mismatches**

#### **Problem:**
```
function trigger_webhook_delivery(text[], text, jsonb, uuid, unknown, unknown, unknown, uuid) does not exist
```

#### **Root Cause:**
Calling webhook delivery function with wrong parameter types or count.

#### **Investigation:**
Check function signature:
```sql
SELECT proname, oidvectortypes(proargtypes) as argument_types 
FROM pg_proc 
WHERE proname = 'trigger_webhook_delivery';
```

#### **Solution:**
Match exact parameter types:
```sql
-- If function expects: (text, jsonb, uuid, uuid, uuid, uuid, uuid)
PERFORM trigger_webhook_delivery(
    event_type_var,    -- text
    event_data_var,    -- jsonb  
    dist_id,           -- uuid
    NULL::uuid,        -- uuid (explicit casting)
    NULL::uuid,        -- uuid
    NULL::uuid,        -- uuid
    NEW.id             -- uuid
);
```

---

### **Issue 4: Data Structure Interface Mismatches**

#### **Problem:**
Frontend form data doesn't align with API expected format.

#### **Root Cause:**
Different interfaces between form components and API functions.

#### **Example:**
```typescript
// Form uses this structure
interface BusinessData {
  businessName: string;
  businessLogo: string;
}

// API expects this structure  
interface CreateCustomerData {
  businessName: string;
  avatar: string;  // Different field name!
}
```

#### **Solution:**
Create proper data mapping:
```typescript
const handleSubmit = async (action: 'invite' | 'save') => {
  // Convert form data to API format
  const apiData: CreateCustomerData = {
    businessName: formData.businessName,
    businessCode: formData.businessCode,
    businessLocation: formData.businessLocation,
    businessLogo: formData.businessLogo,
    
    // Map primary contact data
    customerName: formData.contacts[0].name,
    phone: formData.contacts[0].phone,
    email: formData.contacts[0].email,
    preferredContact: formData.contacts[0].preferredContact,
    
    // Legacy compatibility fields
    avatar: formData.businessLogo,        // Same as businessLogo
    customerCode: formData.businessCode,  // Same as businessCode
    
    labels: formData.labels
  };
  
  await onSaveCustomer(apiData);
};
```

---

## 🛠️ Debugging Workflow

### **Step 1: Add Comprehensive Logging**
```typescript
// In API functions
console.log('🎯 [API] Input data:', inputData);
console.log('🎯 [API] Mapped for DB:', dbInsertData);
console.log('🎯 [API] DB Response:', response);

// In form components  
console.log('🎯 [Form] Form data:', formData);
console.log('🎯 [Form] Converted data:', convertedData);
```

### **Step 2: Check Database Schema**
```sql
-- Get table structure
\d+ table_name

-- Get column details
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'table_name';
```

### **Step 3: Test Database Operations Directly**
```sql
-- Test insert with sample data
INSERT INTO customers (
  distributor_id,
  business_name,
  contact_person_name,
  customer_code,
  email,
  phone,
  address,
  avatar_url,
  status,
  invitation_status,
  joined_date,
  total_orders,
  total_spent
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Test Business',
  'Test Contact',
  'TST123',
  'test@example.com',
  '+1234567890',
  'Test Address',
  'https://example.com/avatar.png',
  'NO_ORDERS_YET',
  'ACTIVE',
  NOW(),
  0,
  0
);
```

### **Step 4: Isolate Issues**
1. **Disable triggers temporarily** to test basic insert:
   ```sql
   DROP TRIGGER IF EXISTS trigger_name ON table_name;
   ```

2. **Test with minimal data** to identify required fields

3. **Re-enable triggers one by one** to isolate problematic triggers

---

## 📋 Best Practices

### **1. Data Type Safety**
- Always match database schema exactly
- Use explicit type casting: `NULL::uuid` instead of `NULL`
- Handle undefined values: `value || null`

### **2. Error Handling**
- Implement custom error classes with user-friendly messages
- Log detailed error information for debugging
- Provide specific error messages for different failure types

### **3. Database Triggers**
- Design triggers to handle all table types they're applied to
- Use `CASE TG_TABLE_NAME` to provide table-specific logic
- Test triggers with all affected tables

### **4. Development Workflow**
- Test database operations in isolation first
- Add comprehensive logging during development
- Use development distributors/users for testing
- Document trigger dependencies and webhook requirements

---

## 🎯 Customer Table Integration Checklist

When connecting a new frontend form to the customers table:

- [ ] **Schema Check**: Verify all field types match database schema
- [ ] **Data Mapping**: Create proper mapping between form and API interfaces
- [ ] **Null Handling**: Handle optional fields with `|| null`
- [ ] **Date Formatting**: Use full ISO timestamps for timestamp fields
- [ ] **UUID Handling**: Ensure proper UUID format for ID fields
- [ ] **Trigger Testing**: Test with triggers enabled
- [ ] **Webhook Testing**: Verify webhook deliveries work correctly
- [ ] **Error Handling**: Implement user-friendly error messages
- [ ] **Logging**: Add debugging logs for troubleshooting

---

## 📚 Related Documentation

- [Database Schema Guide](./database-schema-guide.md)
- [Supabase Connection Guide](./supabase-connection-guide.md)
- [Database Relationships Diagram](./database-relationships-diagram.md)

---

*Last Updated: July 24, 2025*
*Based on: Customer table integration experience*