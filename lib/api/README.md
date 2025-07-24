# API Structure & Conventions

This directory contains all API functions for interacting with Supabase and other external services.

## 📁 Directory Structure

```
/lib/api/
├── customers.ts     # Customer CRUD operations
├── orders.ts        # Order operations (future)
├── auth.ts          # Authentication operations (future)
├── types.ts         # Shared API types (future)
└── README.md        # This file
```

## 🎯 API Conventions

### **Error Handling Pattern**
All API functions follow a consistent error handling pattern:

```typescript
// 1. Define user-friendly error messages
export const ERROR_MESSAGES = {
  DUPLICATE_EMAIL: 'A record with this email already exists',
  NETWORK_ERROR: 'Connection failed. Please check your internet and try again',
  UNKNOWN_ERROR: 'Something went wrong. Please try again'
} as const;

// 2. Create custom error class
export class CustomError extends Error {
  constructor(
    message: string,
    public code: keyof typeof ERROR_MESSAGES,
    public originalError?: any
  ) {
    super(message);
    this.name = 'CustomError';
  }
}

// 3. Handle Supabase errors consistently
function handleSupabaseError(error: any): CustomError {
  if (error.code === '23505') { // Unique constraint violation
    return new CustomError(ERROR_MESSAGES.DUPLICATE_EMAIL, 'DUPLICATE_EMAIL', error);
  }
  return new CustomError(ERROR_MESSAGES.UNKNOWN_ERROR, 'UNKNOWN_ERROR', error);
}

// 4. Use in API functions
export async function apiFunction() {
  try {
    const { data, error } = await supabase.from('table').select();
    if (error) throw handleSupabaseError(error);
    return data;
  } catch (error) {
    if (error instanceof CustomError) throw error;
    throw handleSupabaseError(error);
  }
}
```

### **Logging Pattern**
Use consistent logging with emoji prefixes:

```typescript
console.log('🎯 [API] Operation started:', data);     // Info
console.warn('⚠️ [API] Warning occurred:', warning);   // Warning  
console.error('🚨 [API] Error occurred:', error);      // Error
```

### **Data Mapping Pattern**
Always provide mapping functions between database and frontend formats:

```typescript
// Database row to frontend type
function mapDatabaseToFrontend(dbRow: DatabaseRow): FrontendType {
  return {
    id: dbRow.id,
    name: dbRow.display_name,
    // ... other mappings
  };
}

// Frontend type to database insert
function mapFrontendToDatabase(frontendData: FrontendType): DatabaseInsert {
  return {
    display_name: frontendData.name,
    // ... other mappings
  };
}
```

### **Function Naming**
- `get*()` - Fetch single or multiple records
- `create*()` - Insert new records  
- `update*()` - Modify existing records
- `delete*()` - Remove records
- `map*()` - Transform data between formats

### **TypeScript Conventions**
- Export all interfaces used by API functions
- Use Supabase generated types: `Database['public']['Tables']['table']['Row']`
- Provide JSDoc comments for all exported functions
- Use strict typing - avoid `any` where possible

## 🔧 Development Patterns

### **Multi-tenant Data Access**
All API functions must respect distributor isolation:

```typescript
function getCurrentDistributorId(): string {
  // TODO: Get from auth context when available
  return DEV_DISTRIBUTORS[0].id; // Development mode
}

// Always filter by distributor
const { data } = await supabase
  .from('table')
  .select('*')
  .eq('distributor_id', getCurrentDistributorId());
```

### **Label/Relationship Handling**
When dealing with related data (labels, assignments):

```typescript
// 1. Fetch main records
const { data: records } = await supabase.from('main_table').select('*');

// 2. Fetch related data in batch
const recordIds = records.map(r => r.id);
const { data: relationships } = await supabase
  .from('relationship_table')
  .select('*, related_table(*)')
  .in('main_id', recordIds);

// 3. Group and map relationships
const relationshipsByRecord = groupBy(relationships, 'main_id');
return records.map(record => ({
  ...record,
  relationships: relationshipsByRecord[record.id] || []
}));
```

## 📋 Migration from Mock Data

When migrating from mock data to Supabase:

1. **Create new API file** in `/lib/api/`
2. **Implement Supabase functions** following these conventions
3. **Update import statements** in components
4. **Add deprecation warnings** to mock functions
5. **Test thoroughly** before removing mock functions

## 🧪 Development Mode

All API functions support development mode with:
- Placeholder authentication using `DEV_DISTRIBUTORS`
- Detailed console logging for debugging
- Error simulation for testing error handling

## 🎯 Future Enhancements

- Authentication integration with `useAuth()` hook
- Caching layer for frequently accessed data
- Optimistic updates for better UX
- Background sync capabilities
- Rate limiting and retry logic