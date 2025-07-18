# INITIAL.md – Messages Page with AI Agent Integration

<!--
This file defines the Messages/Chats feature for the Reddi platform.
The Messages page enables seamless communication between distributors and customers with AI-powered assistance.
-->

## Feature

**AI-Powered Messages Dashboard**

Build a comprehensive **Messages** page that centralizes all customer communications across channels (WhatsApp, SMS, Email) with integrated AI agent capabilities powered by OpenAI API. The goal is to capture every order, everywhere.

User goals:

1. **Unified Communication Hub** – View all customer conversations in a single interface, organized by customer and channel
2. **AI Assistant Integration** – Leverage OpenAI API to provide intelligent message suggestions, automated responses, and order processing assistance
3. **Contextual Order Management** – Seamlessly transition from messages to order creation/confirmation without leaving the conversation context
4. **Real-time Message Handling** – Process incoming messages with AI-powered categorization and suggested responses

### Functional Spec

| Element | Details |
|---------|---------|
| **Chat List Panel** | Left sidebar showing all active conversations with customer avatars, last message preview, unread counts, and channel indicators |
| **Message Thread View** | Central area displaying selected conversation with message history, timestamps, and delivery status |
| **AI Assistant Panel** | Right sidebar with OpenAI-powered features: message suggestions, order processing, customer insights |
| **Message Input Area** | Rich text input with file attachments, AI suggestion integration, and send options |
| **Channel Integration** | Native support for WhatsApp, SMS, and Email with channel-specific message formatting |
| **Order Context Cards** | Inline order summaries and quick actions when orders are referenced in messages |

### Visual Spec

* **Design Continuity**: Pixel-match the existing Orders and Customers pages design system
* **Chat Interface**: Inspired by `/design/references/messages_page.png`
* **Color Scheme**: Consistent with current platform using `design/tokens.md` palette
* **Layout**: Three-column layout (Chat List | Message Thread | AI Assistant) with responsive collapse on mobile

## Examples

Reference existing implementation patterns:
- `/app/orders/page.tsx` - Table structure, pagination, and filtering patterns
- `/app/customers/page.tsx` - Customer data handling and panel interactions
- `/components/` - Reusable UI components and styling conventions
- `/agent-platform/` - Pydantic AI agent patterns with MCP integration

## Documentation

**Project Documentation:**
- `/documentation/technical-spec.md` – Detailed AI architecture, database schema, and Pydantic AI implementation
- `/documentation/setup-guide.md` – Complete environment setup, dependencies, and development workflow
- `/documentation/security-guide.md` – Multi-tenant security, PII protection, and compliance guidelines

**External References:**
1. **Next.js 14 App Router** – https://nextjs.org/docs/app
2. **Tailwind CSS** – https://tailwindcss.com/docs  
3. **Pydantic AI** – https://ai.pydantic.dev/
4. **OpenAI API** – https://platform.openai.com/docs/api-reference
5. **design/tokens.md** – Existing design system tokens
6. **Lucide Icons** – https://lucide.dev

## Other Considerations

- **AI Architecture**: Use existing `agent-platform/` framework with Pydantic AI agents and MCP tools
- **Database**: Multi-tenant Supabase database already created with 16 tables for AI-powered operations
- **Security**: All data isolated by `distributor_id` with Row Level Security (RLS) policies
- **Real-time**: WebSocket integration for live message updates and typing indicators
- **File Structure**: Follow established patterns with `/app/messages/`, `/backend/agents/`, and MCP integration

**Required File Structure:**
```
/app/messages/page.tsx
/app/messages/components/ChatList.tsx
/app/messages/components/MessageThread.tsx
/app/messages/components/AIAssistantPanel.tsx
/backend/agents/message_analysis.py
/backend/agents/order_processing.py
/backend/agents/customer_support.py
```

**Type Safety:**
```ts
interface Message {
  id: string;
  conversationId: string;
  content: string;
  isFromCustomer: boolean;
  messageType: 'TEXT' | 'IMAGE' | 'AUDIO' | 'ORDER_CONTEXT';
  aiProcessed: boolean;
  aiConfidence?: number;
  createdAt: string;
}
```

*Commit message suggestion*:  
`feat: Messages page with Pydantic AI agents, multi-tenant database, and MCP integration`

## Setup Prerequisites

**Frontend Dependencies:**
```bash
npm install @supabase/supabase-js socket.io-client @tanstack/react-query
```

**Backend Dependencies:**
```bash
pip install fastapi pydantic-ai openai supabase
```

**MCP Configuration:**
- Use existing `/agent-platform/mcp_config.json` (Supabase + Context7)
- Database tables already created via `/supabase/migrations/`