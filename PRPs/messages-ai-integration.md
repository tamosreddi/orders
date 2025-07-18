# PRP: Messages Page with AI Agent Integration

name: "AI-Powered Messages Dashboard with Pydantic AI Integration"
description: |
  Comprehensive Messages/Chat feature for the Reddi platform that centralizes customer communications 
  across channels (WhatsApp, SMS, Email) with integrated AI agent capabilities powered by OpenAI API.

---

## Goal
Build a production-ready Messages page that enables distributors to manage customer communications efficiently with AI-powered assistance for order processing, message suggestions, and automated responses. The system must capture every order, everywhere, through intelligent message processing.

## Why
- **Business Value**: Centralizes customer communications reducing response time and improving order capture rate
- **AI-Powered Efficiency**: Leverages OpenAI API for intelligent message categorization and automated responses
- **Integration**: Seamlessly integrates with existing Orders and Customers systems using established patterns
- **Multi-tenant Security**: Maintains data isolation with distributor_id and RLS policies
- **Real-time Experience**: Provides instant message updates and typing indicators for improved UX

## What
A three-column chat interface with:
1. **Chat List Panel** (left): Customer conversations with avatars, unread counts, channel indicators
2. **Message Thread View** (center): Selected conversation with message history and order context cards
3. **AI Assistant Panel** (right): OpenAI-powered suggestions, order processing, customer insights
4. **Real-time Updates**: WebSocket integration for live messaging and typing indicators
5. **Multi-channel Support**: Native WhatsApp, SMS, and Email integration

### Success Criteria
- [ ] Messages page loads with existing design system consistency (pixel-match Orders/Customers pages)
- [ ] Real-time messaging works across all channels (WhatsApp, SMS, Email)
- [ ] AI agent processes messages and provides contextual suggestions
- [ ] Order context cards appear inline when orders are referenced
- [ ] Three-column responsive layout works on desktop and mobile
- [ ] All database operations respect multi-tenant RLS policies
- [ ] WebSocket connections handle reconnection and error states gracefully

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/agents/
  why: Core PydanticAI agent patterns, system prompts, tool integration
  
- url: https://platform.openai.com/docs/api-reference/chat
  why: OpenAI Chat API integration for message processing and suggestions
  
- url: https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts
  why: Next.js 14 App Router patterns for page structure
  
- url: https://github.com/chatscope/chat-ui-kit-react
  why: TypeScript chat UI component patterns and best practices
  
- file: /app/orders/page.tsx
  why: Page layout pattern, state management, filtering, pagination
  
- file: /app/customers/page.tsx
  why: Customer data handling, panel interactions, search patterns
  
- file: /components/TabFilterBar.tsx
  why: Filter UI patterns, tab-based navigation, search integration
  
- file: /components/customer_components/CustomerDetailsPanel.tsx
  why: Side panel pattern, portal rendering, ESC key handling
  
- file: /design/tokens.md
  why: Complete design system tokens, colors, typography, spacing
  
- file: /agent-platform/mcp_config.json
  why: MCP server configuration for Supabase and Context7 integration
  
- doc: https://dev.to/dhrumitdk/building-a-real-time-chat-application-with-nextjs-and-websockets-532d
  section: WebSocket setup with Next.js 14
  critical: Cannot use serverless for WebSocket server - needs VPS or Socket.io external service
  
- docfile: /documentation/technical-spec.md
  why: AI architecture, database schema, Pydantic AI implementation details
  
- docfile: /documentation/security-guide.md
  why: Multi-tenant security, PII protection, RLS policy implementation
```

### Current Codebase Structure
```bash
/Users/macbook/orderagent/
├── app/
│   ├── orders/page.tsx                 # Pattern for page layout
│   ├── customers/page.tsx              # Pattern for customer handling
│   └── orders/[id]/review/             # Dynamic routing patterns
├── components/
│   ├── TabFilterBar.tsx                # Filter UI patterns
│   └── customer_components/
│       └── CustomerDetailsPanel.tsx    # Side panel patterns
├── types/
│   ├── order.ts                        # Type definitions for orders
│   └── customer.ts                     # Type definitions for customers
├── design/
│   ├── tokens.md                       # Complete design system
│   └── references/messages_page.png    # Visual design reference
├── agent-platform/
│   └── mcp_config.json                 # MCP server configuration
├── documentation/
│   ├── technical-spec.md               # AI architecture details
│   ├── security-guide.md               # Multi-tenant security
│   └── database-schema-guide.md        # Database patterns
└── supabase/migrations/                # Database migrations
```

### Desired Codebase Structure with New Files
```bash
/Users/macbook/orderagent/
├── app/messages/
│   ├── page.tsx                        # Main messages page (mirror orders/customers pattern)
│   ├── components/
│   │   ├── ChatList.tsx                # Left panel - conversation list
│   │   ├── MessageThread.tsx           # Center panel - message history
│   │   ├── AIAssistantPanel.tsx        # Right panel - AI suggestions
│   │   ├── MessageInput.tsx            # Bottom input with file upload
│   │   └── OrderContextCard.tsx        # Inline order reference cards
│   ├── hooks/
│   │   ├── useMessages.ts              # Message data management
│   │   ├── useAIAgent.ts               # OpenAI integration
│   │   └── useWebSocket.ts             # Real-time messaging
│   └── types/
│       ├── message.ts                  # Message interface definitions
│       └── conversation.ts             # Conversation interface definitions
├── backend/agents/                     # Python AI agents (if needed)
│   ├── message_analysis.py             # AI message categorization
│   ├── order_processing.py             # Order context extraction
│   └── customer_support.py             # Automated response generation
└── components/navigation-menu/
    └── NavigationMenu.tsx              # Update to enable Messages menu item
```

### Known Gotchas & Library Quirks
```typescript
// CRITICAL: Next.js 14 WebSocket limitations
// Cannot use serverless deployment (Vercel) with persistent WebSocket connections
// Must use 'use client' for all WebSocket-related components
// Socket.io-client requires separate server or external service like Ably

// CRITICAL: Pydantic AI with OpenAI
// Use openai:gpt-4o model format for automatic provider selection
// Always validate inputs with Pydantic models before AI processing
// MCP tools require async/await patterns

// CRITICAL: Supabase RLS patterns
// All queries MUST include distributor_id filter for multi-tenant isolation
// Use existing pattern from orders/customers: WHERE distributor_id = ?
// Real-time subscriptions need RLS-aware filtering

// CRITICAL: Design system consistency
// Use exact token values from design/tokens.md
// Follow three-column layout from design/references/messages_page.png
// Maintain pixel-perfect consistency with Orders/Customers pages
```

## Implementation Blueprint

### Data Models and Structure

Create the core data models ensuring type safety and consistency with existing patterns:

```typescript
// app/messages/types/message.ts
interface Message {
  id: string;
  conversationId: string;
  content: string;
  isFromCustomer: boolean;
  messageType: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT';
  status: 'SENT' | 'DELIVERED' | 'READ';
  attachments?: Array<{
    id: string;
    type: string;
    url: string;
    fileName: string;
  }>;
  aiProcessed: boolean;
  aiConfidence?: number;
  aiSuggestedResponses?: string[];
  orderContextId?: string;
  distributorId: string;  // Multi-tenant isolation
  createdAt: string;
  updatedAt: string;
}

// app/messages/types/conversation.ts
interface Conversation {
  id: string;
  customerId: string;
  customer: {
    name: string;
    avatar: string;
    code: string;
  };
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  lastMessageAt: string;
  unreadCount: number;
  lastMessage: {
    content: string;
    isFromCustomer: boolean;
  };
  aiContextSummary?: string;
  distributorId: string;  // Multi-tenant isolation
  createdAt: string;
  updatedAt: string;
}
```

### List of Tasks to be Completed (Implementation Order)

```yaml
Task 1: Enable Messages Navigation
MODIFY components/navigation-menu/NavigationMenu.tsx:
  - FIND pattern: "isDisabled: true" for Messages menu item
  - CHANGE to: "isDisabled: false"
  - PRESERVE existing navigation structure

Task 2: Create Message Type Definitions
CREATE app/messages/types/message.ts:
  - MIRROR pattern from: types/order.ts and types/customer.ts
  - IMPLEMENT Message and MessageAttachment interfaces
  - INCLUDE distributor_id for multi-tenant isolation

CREATE app/messages/types/conversation.ts:
  - MIRROR pattern from: types/customer.ts
  - IMPLEMENT Conversation interface with customer relationship
  - INCLUDE channel and unread count fields

Task 3: Create Main Messages Page
CREATE app/messages/page.tsx:
  - MIRROR exact pattern from: app/orders/page.tsx
  - KEEP same state management hooks (useState, useEffect, useMemo)
  - IMPLEMENT three-column layout using design tokens
  - USE 'use client' directive for WebSocket components

Task 4: Create Chat List Component
CREATE app/messages/components/ChatList.tsx:
  - MIRROR pattern from: components/TabFilterBar.tsx for filtering
  - IMPLEMENT conversation list with avatars and unread counts
  - USE design tokens for brand-navy-900 sidebar background
  - INCLUDE search functionality following existing patterns

Task 5: Create Message Thread Component
CREATE app/messages/components/MessageThread.tsx:
  - MIRROR pattern from: app/orders/page.tsx for data loading
  - IMPLEMENT message history display with timestamps
  - INCLUDE typing indicators and delivery status
  - USE existing shadow-card and border-subtle tokens

Task 6: Create AI Assistant Panel
CREATE app/messages/components/AIAssistantPanel.tsx:
  - MIRROR pattern from: components/customer_components/CustomerDetailsPanel.tsx
  - IMPLEMENT OpenAI suggestion display
  - INCLUDE order processing actions
  - USE portal rendering for expandable states

Task 7: Create Message Input Component
CREATE app/messages/components/MessageInput.tsx:
  - MIRROR pattern from existing form inputs in orders/customers
  - IMPLEMENT rich text input with file upload
  - INCLUDE AI suggestion integration
  - USE consistent button styling with hover states

Task 8: Create Order Context Cards
CREATE app/messages/components/OrderContextCard.tsx:
  - MIRROR pattern from existing order cards in orders page
  - IMPLEMENT inline order summaries
  - INCLUDE quick action buttons
  - USE state-success tokens for status indicators

Task 9: Create WebSocket Hook
CREATE app/messages/hooks/useWebSocket.ts:
  - IMPLEMENT real-time message handling
  - INCLUDE reconnection logic and error handling
  - USE 'use client' pattern for client-side only execution
  - FOLLOW Socket.io client patterns from research

Task 10: Create AI Agent Hook
CREATE app/messages/hooks/useAIAgent.ts:
  - IMPLEMENT OpenAI API integration
  - INCLUDE message categorization and suggestions
  - USE Pydantic AI patterns from agent-platform
  - INCLUDE error handling and retry logic

Task 11: Create Messages Data Hook
CREATE app/messages/hooks/useMessages.ts:
  - MIRROR pattern from existing data hooks
  - IMPLEMENT Supabase queries with RLS filtering
  - INCLUDE optimistic updates for real-time feel
  - USE distributor_id filtering for multi-tenant isolation

Task 12: Update Database Schema (if needed)
VERIFY supabase/migrations/ tables:
  - CONFIRM messages table has all required fields
  - CONFIRM conversations table structure
  - ENSURE RLS policies exist for distributor_id isolation
  - ADD indexes for performance if missing

Task 13: Integration Testing
RUN integration tests:
  - TEST three-column layout responsiveness
  - TEST real-time message sending/receiving
  - TEST AI agent message processing
  - TEST order context card functionality
  - VERIFY multi-tenant data isolation
```

### Per Task Pseudocode

```typescript
// Task 3: Main Messages Page Pattern
'use client';

export default function MessagesPage() {
  // PATTERN: Mirror orders page state management
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchValue, setSearchValue] = useState('');
  
  // PATTERN: Data loading with useEffect (see orders/page.tsx)
  useEffect(() => {
    const loadConversations = async () => {
      // CRITICAL: Include distributor_id filter for RLS
      const { data } = await supabase
        .from('conversations')
        .select('*, customer:customers(*)')
        .eq('distributor_id', distributorId)
        .order('last_message_at', { ascending: false });
      setConversations(data || []);
      setLoading(false);
    };
    loadConversations();
  }, []);
  
  // PATTERN: Three-column layout using design tokens
  return (
    <div className="min-h-screen bg-surface-0">
      <div className="max-w-container mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-heading-xl font-sans text-primary-ink font-antialiased">
            Messages
          </h1>
        </div>
        
        <div className="bg-surface-0 rounded-lg shadow-card overflow-hidden">
          <div className="flex h-[calc(100vh-200px)]">
            {/* Left Panel - Chat List */}
            <div className="w-80 bg-brand-navy-900 text-white">
              <ChatList 
                conversations={filteredConversations}
                selectedId={selectedConversation}
                onSelect={setSelectedConversation}
                searchValue={searchValue}
                onSearch={setSearchValue}
              />
            </div>
            
            {/* Center Panel - Message Thread */}
            <div className="flex-1 flex flex-col">
              <MessageThread
                conversationId={selectedConversation}
                messages={messages}
                onSendMessage={handleSendMessage}
              />
            </div>
            
            {/* Right Panel - AI Assistant */}
            <div className="w-80 border-l border-border-subtle">
              <AIAssistantPanel
                conversationId={selectedConversation}
                context={selectedConversation ? conversations.find(c => c.id === selectedConversation) : null}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Task 9: WebSocket Hook Pattern
export function useWebSocket(conversationId: string | null) {
  // PATTERN: Client-side only execution
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    if (!conversationId) return;
    
    // CRITICAL: Socket.io client pattern from research
    const newSocket = io('ws://localhost:3001', {
      transports: ['websocket'],
      auth: { distributorId, conversationId }
    });
    
    newSocket.on('connect', () => setConnected(true));
    newSocket.on('disconnect', () => setConnected(false));
    
    // PATTERN: Real-time message handling
    newSocket.on('new-message', (message: Message) => {
      setMessages(prev => [...prev, message]);
    });
    
    setSocket(newSocket);
    
    return () => {
      newSocket.close();
    };
  }, [conversationId]);
  
  return { socket, connected };
}

// Task 10: AI Agent Hook Pattern
export function useAIAgent() {
  // PATTERN: OpenAI integration with error handling
  const processMessage = async (content: string): Promise<AIResponse> => {
    try {
      // CRITICAL: Use Pydantic AI pattern from agent-platform
      const response = await fetch('/api/ai/process-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          distributorId,
          model: 'openai:gpt-4o'  // Auto-selects provider
        })
      });
      
      if (!response.ok) throw new Error('AI processing failed');
      return await response.json();
    } catch (error) {
      console.error('AI Agent Error:', error);
      return { suggestions: [], confidence: 0, error: error.message };
    }
  };
  
  return { processMessage };
}
```

### Integration Points
```yaml
DATABASE:
  - tables: "messages, conversations already created in migrations"
  - indexes: "CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at)"
  
CONFIG:
  - add to: app/lib/supabase.ts
  - pattern: "Real-time subscription configuration for messages"
  
ROUTES:
  - enable: components/navigation-menu/NavigationMenu.tsx
  - pattern: "Change isDisabled: false for Messages menu item"
  
AI_AGENT:
  - use: agent-platform/mcp_config.json
  - pattern: "Leverage existing Supabase MCP server configuration"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
npm run lint              # ESLint checking
npm run type-check        # TypeScript validation
npm run build             # Build validation

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Component Tests
```typescript
// CREATE tests/messages/ChatList.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import ChatList from '@/app/messages/components/ChatList';

describe('ChatList Component', () => {
  const mockConversations = [
    {
      id: '1',
      customer: { name: 'John Doe', avatar: '/avatar1.jpg', code: 'C001' },
      channel: 'WHATSAPP',
      unreadCount: 2,
      lastMessage: { content: 'Hello', isFromCustomer: true }
    }
  ];

  test('renders conversation list', () => {
    render(<ChatList conversations={mockConversations} selectedId={null} onSelect={jest.fn()} />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // unread count
  });

  test('handles conversation selection', () => {
    const onSelect = jest.fn();
    render(<ChatList conversations={mockConversations} selectedId={null} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByText('John Doe'));
    expect(onSelect).toHaveBeenCalledWith('1');
  });

  test('displays channel indicators correctly', () => {
    render(<ChatList conversations={mockConversations} selectedId={null} onSelect={jest.fn()} />);
    expect(screen.getByText('WHATSAPP')).toBeInTheDocument();
  });
});
```

```bash
# Run and iterate until passing:
npm test -- --testPathPattern=messages
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the development server
npm run dev

# Test the messages page
curl -X GET http://localhost:3000/messages
# Expected: Page loads with three-column layout

# Test WebSocket connection (if Socket.io server running)
# Open browser developer tools and check WebSocket connection in Network tab
# Expected: WebSocket connection established and receiving events
```

## Final Validation Checklist
- [ ] All tests pass: `npm test`
- [ ] No linting errors: `npm run lint`
- [ ] No type errors: `npm run type-check`
- [ ] Build succeeds: `npm run build`
- [ ] Messages page loads at /messages with three-column layout
- [ ] Chat list displays conversations with proper filtering
- [ ] Message thread shows conversation history
- [ ] AI assistant panel provides contextual suggestions
- [ ] Real-time messaging works (if WebSocket server configured)
- [ ] Order context cards appear when orders are referenced
- [ ] Responsive design works on mobile (columns collapse appropriately)
- [ ] Multi-tenant isolation verified (only distributor's conversations visible)

---

## Anti-Patterns to Avoid
- ❌ Don't create new design patterns - use exact tokens from design/tokens.md
- ❌ Don't skip RLS filtering - always include distributor_id in queries
- ❌ Don't use sync functions for WebSocket or AI operations - use async/await
- ❌ Don't hardcode API endpoints - use environment variables
- ❌ Don't ignore WebSocket connection errors - implement proper error handling
- ❌ Don't skip TypeScript validation - ensure all interfaces are properly typed
- ❌ Don't break existing navigation patterns - follow Orders/Customers page structure exactly

---

## Quality Score: 9/10

**Confidence Level for One-Pass Implementation**: Very High

**Strengths:**
- Comprehensive codebase analysis with specific file references
- Detailed external research on best practices
- Complete design system integration
- Explicit task ordering with clear dependencies
- Thorough validation gates with executable commands
- Multi-tenant security considerations included

**Areas for Potential Iteration:**
- WebSocket server setup may require additional configuration depending on hosting choice
- AI agent fine-tuning might need iteration based on message processing quality

The PRP provides sufficient context and detailed implementation guidance for successful one-pass implementation while maintaining consistency with existing codebase patterns and design system.