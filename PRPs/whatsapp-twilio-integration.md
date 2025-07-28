name: "WhatsApp Twilio Sandbox Integration PRP"
description: |

## Purpose
Comprehensive PRP for implementing WhatsApp messaging through Twilio Sandbox API with webhook handling, database persistence, and real-time UI updates. Optimized for AI agents to achieve working code through iterative refinement with full context and validation loops.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a complete WhatsApp messaging pipeline that receives messages from Twilio Sandbox via webhook, stores them in Supabase database with proper multi-tenant isolation, and displays them in real-time on the existing Messages page UI.

## Why
- **Demo Value**: Showcase AI-powered order processing through natural WhatsApp conversations
- **Business Impact**: Enable customers to place orders via WhatsApp without learning new interfaces
- **Integration Foundation**: Establish webhook patterns for future messaging channel integrations
- **AI Pipeline Ready**: Messages stored in database become immediately available for AI processing using existing infrastructure

## What
A complete WhatsApp integration consisting of:
1. **Webhook Handler**: Secure API endpoint receiving Twilio webhook requests
2. **Database Operations**: Multi-tenant customer/conversation/message management
3. **Real-time UI**: Polling-based message updates in existing Messages page
4. **Configuration**: Environment setup for Twilio Sandbox testing

### Success Criteria
- [ ] Customers can send WhatsApp messages to Twilio Sandbox number and see them appear in Messages page
- [ ] All messages are properly stored with multi-tenant isolation (distributor_id filtering)
- [ ] New customers are automatically created from unknown phone numbers
- [ ] Conversations are properly threaded by customer and channel
- [ ] Messages display in real-time (2-second polling) using existing UI components
- [ ] Webhook security validation prevents unauthorized requests
- [ ] All TypeScript types are properly defined and error-free

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://www.twilio.com/docs/whatsapp/sandbox
  why: Complete WhatsApp Sandbox setup, webhook configuration, and message format documentation
  
- url: https://www.twilio.com/docs/messaging/guides/webhook-request
  why: Webhook payload structure, required parameters, and TwiML response format
  
- url: https://www.twilio.com/docs/usage/webhooks/webhooks-security
  why: Critical signature validation process for webhook security - MUST implement
  
- url: https://supabase.com/docs/reference/javascript/upsert
  why: Upsert patterns for customer/conversation creation without conflicts

- file: /lib/api/customers.ts
  why: Error handling patterns, multi-tenancy filtering, and database operation structure to mirror
  
- file: /app/messages/hooks/useMessages.ts
  why: Existing data fetching patterns, real-time subscription setup, and state management
  
- file: /app/messages/components/MessageThread.tsx
  why: UI component patterns for message display, styling, and interaction handling
  
- file: /supabase/migrations/20240717120014_add_webhook_integration.sql
  why: Existing webhook infrastructure (webhook_endpoints, webhook_deliveries tables) to leverage
  
- file: /documentation/database/database-schema-guide.md
  why: Complete database schema understanding, especially conversations/messages/customers tables

- docfile: /app/messages/types/message.ts
  why: Existing TypeScript interfaces for Message and Conversation entities to extend
```

### Current Codebase Tree (Relevant Sections)
```bash
/Users/macbook/orderagent/
├── app/
│   ├── api/                          # No existing API routes - need to create pattern
│   └── messages/
│       ├── components/
│       │   ├── MessageThread.tsx     # Main message display component
│       │   └── ChatList.tsx          # Conversation list component
│       ├── hooks/
│       │   └── useMessages.ts        # Data fetching and real-time updates
│       ├── types/
│       │   ├── message.ts            # Message/Conversation TypeScript interfaces
│       │   └── conversation.ts
│       └── page.tsx                  # Main Messages page
├── lib/
│   ├── api/
│   │   └── customers.ts              # Pattern for database operations and error handling
│   └── supabase/
│       ├── client.ts                 # Configured Supabase client
│       └── types.ts                  # Generated database types
├── supabase/migrations/
│   ├── 20240716120002_create_conversations_table.sql
│   ├── 20240716120003_create_messages_table.sql
│   └── 20240717120014_add_webhook_integration.sql  # Webhook infrastructure
└── types/
    └── customer.ts                   # Existing type patterns
```

### Desired Codebase Tree with New Files
```bash
/Users/macbook/orderagent/
├── app/api/webhooks/twilio/
│   └── route.ts                      # NEW: Webhook handler with signature validation
├── lib/api/
│   └── whatsapp.ts                   # NEW: WhatsApp-specific database operations
├── lib/utils/
│   └── twilio.ts                     # NEW: Twilio helper functions and validation
├── types/
│   └── twilio.ts                     # NEW: Twilio webhook payload types
├── tests/
│   ├── api/
│   │   └── twilio-webhook.test.ts    # NEW: Webhook handler tests
│   └── lib/
│       └── whatsapp.test.ts          # NEW: Database operations tests
└── .env.example                      # UPDATED: Add Twilio credentials
```

### Known Gotchas of Our Codebase & Library Quirks
```typescript
// CRITICAL: Supabase doesn't support client-side database transactions
// Must use individual operations with proper error handling - see lib/api/customers.ts pattern

// CRITICAL: Multi-tenancy isolation is MANDATORY
// Every database operation MUST include distributor_id filtering - see existing patterns

// CRITICAL: Phone number format for WhatsApp
// Twilio sends: "whatsapp:+1234567890" - need to parse and store properly

// CRITICAL: Twilio signature validation requires EXACT URL match
// Including protocol, domain, path, and query parameters - see webhook security docs

// CRITICAL: Next.js 14 App Router API routes pattern
// Use export async function POST(request: Request) - no existing examples in codebase

// CRITICAL: Existing message polling pattern uses 2-second intervals
// Don't change without updating the initial requirements - see useMessages.ts

// CRITICAL: TwiML response format required
// Twilio expects XML response, not JSON - must return proper Content-Type

// CRITICAL: Error handling follows CustomerError pattern
// Use ERROR_MESSAGES constants and specific error codes - see lib/api/customers.ts
```

## Implementation Blueprint

### Data Models and Structure

Create type-safe interfaces for Twilio integration:
```typescript
// types/twilio.ts - NEW FILE
export interface TwilioWebhookPayload {
  From: string;           // "whatsapp:+1234567890"
  To: string;             // "whatsapp:+14155238886"
  Body: string;           // Message content
  MessageSid: string;     // "SMxxxxxxxxxxxx"
  AccountSid: string;     // "ACxxxxxxxxxxxx"
  NumMedia: string;       // "0" or number as string
  MediaUrl0?: string;     // First media URL if present
  MediaContentType0?: string; // MIME type of first media
  Timestamp: string;      // ISO timestamp
}

export interface WhatsAppMessage {
  id: string;
  conversationId: string;
  content: string;
  isFromCustomer: boolean;
  messageType: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE';
  status: 'SENT' | 'DELIVERED' | 'READ';
  attachments: MessageAttachment[];
  externalMessageId: string; // Twilio MessageSid
  externalMetadata: Record<string, any>; // Raw Twilio payload
  distributorId: string;
  createdAt: string;
}

export interface WhatsAppCustomer {
  phoneNumber: string;    // Parsed from "whatsapp:+1234567890"
  businessName: string;   // Auto-generated or extracted
  contactPersonName: string;
  distributorId: string;
}
```

### List of Tasks to be Completed (In Order)

```yaml
Task 1 - Create Twilio Types and Utilities:
CREATE types/twilio.ts:
  - DEFINE TwilioWebhookPayload interface with all required fields
  - DEFINE WhatsAppMessage interface extending base Message type
  - ADD utility type guards for payload validation

CREATE lib/utils/twilio.ts:
  - IMPLEMENT parsePhoneNumber() function to extract number from "whatsapp:+1234567890"
  - IMPLEMENT validateTwilioSignature() using twilio.validateRequest()
  - IMPLEMENT formatTwiMLResponse() for XML response generation
  - PATTERN: Follow error handling from lib/api/customers.ts

Task 2 - Create WhatsApp Database Service Layer:
CREATE lib/api/whatsapp.ts:
  - MIRROR pattern from: lib/api/customers.ts
  - IMPLEMENT findOrCreateCustomer() with phone number lookup/creation
  - IMPLEMENT findOrCreateConversation() with WHATSAPP channel
  - IMPLEMENT createMessage() with proper distributor_id isolation
  - PRESERVE existing error handling pattern identical
  - USE existing Supabase client from lib/supabase/client.ts

Task 3 - Create Webhook API Route Handler:
CREATE app/api/webhooks/twilio/route.ts:
  - IMPLEMENT POST handler following Next.js 14 App Router pattern
  - ADD Twilio signature validation using lib/utils/twilio.ts
  - PARSE webhook payload and validate required fields
  - CALL WhatsApp service layer functions in sequence
  - RETURN proper TwiML XML response with Content-Type: text/xml
  - HANDLE errors gracefully with proper HTTP status codes

Task 4 - Extend Message Components for WhatsApp:
MODIFY app/messages/hooks/useMessages.ts:
  - FIND existing loadConversations function
  - ADD WhatsApp channel filtering support
  - PRESERVE existing polling pattern (2-second interval)
  - EXTEND conversation query to include WHATSAPP channel

MODIFY app/messages/components/MessageThread.tsx:
  - FIND message rendering logic
  - ADD WhatsApp-specific message display (phone number formatting)
  - PRESERVE existing styling and interaction patterns
  - ADD support for external message metadata display

Task 5 - Add Environment Configuration:
MODIFY .env.example:
  - ADD TWILIO_ACCOUNT_SID=your_account_sid_here
  - ADD TWILIO_AUTH_TOKEN=your_auth_token_here
  - ADD TWILIO_PHONE_NUMBER=+14155238886
  - ADD NEXT_PUBLIC_WEBHOOK_URL=https://yourdomain.com/api/webhooks/twilio

UPDATE README.md:
  - ADD Twilio Sandbox setup instructions
  - ADD ngrok setup for local development
  - ADD testing flow: join sandbox -> send message -> verify in UI

Task 6 - Create Comprehensive Tests:
CREATE tests/api/twilio-webhook.test.ts:
  - TEST webhook payload validation
  - TEST signature validation (mock valid/invalid signatures)
  - TEST customer creation from new phone numbers
  - TEST conversation creation and message insertion
  - TEST error handling for malformed payloads

CREATE tests/lib/whatsapp.test.ts:
  - TEST findOrCreateCustomer with existing/new customers
  - TEST findOrCreateConversation with existing/new conversations
  - TEST createMessage with proper distributor_id isolation
  - TEST phone number parsing utility functions
```

### Per Task Pseudocode Details

```typescript
// Task 1 - Twilio Utilities
// lib/utils/twilio.ts
export function parsePhoneNumber(twilioFormat: string): string {
    // INPUT: "whatsapp:+1234567890"
    // OUTPUT: "+1234567890"
    // PATTERN: Validate format first, then extract
    if (!twilioFormat.startsWith('whatsapp:')) {
        throw new ValidationError('Invalid WhatsApp phone format');
    }
    return twilioFormat.replace('whatsapp:', '');
}

export function validateTwilioSignature(
    authToken: string,
    signature: string,
    url: string,
    params: Record<string, any>
): boolean {
    // CRITICAL: Use Twilio's validateRequest - don't implement custom validation
    // GOTCHA: URL must be EXACT match including protocol and domain
    const twilio = require('twilio');
    return twilio.validateRequest(authToken, signature, url, params);
}

// Task 2 - Database Service Layer
// lib/api/whatsapp.ts
export async function findOrCreateCustomer(
    phoneNumber: string, 
    distributorId: string
): Promise<Customer> {
    // PATTERN: Always validate input first (see lib/api/customers.ts)
    const validated = validatePhoneNumber(phoneNumber);
    
    // PATTERN: Use upsert to handle race conditions
    const { data, error } = await supabase
        .from('customers')
        .upsert({
            phone: validated,
            distributor_id: distributorId,
            business_name: `WhatsApp Customer ${validated}`, // Auto-generated
            contact_person_name: validated,
            status: 'ORDERING'
        }, {
            onConflict: 'phone,distributor_id', // Unique constraint
            ignoreDuplicates: false
        })
        .select()
        .single();
    
    // PATTERN: Standardized error handling (see lib/api/customers.ts)
    if (error) throw handleSupabaseError(error);
    return mapCustomerToFrontend(data);
}

// Task 3 - Webhook Handler
// app/api/webhooks/twilio/route.ts
export async function POST(request: Request) {
    try {
        // CRITICAL: Parse form data (Twilio sends application/x-www-form-urlencoded)
        const formData = await request.formData();
        const payload = Object.fromEntries(formData.entries());
        
        // CRITICAL: Validate Twilio signature for security
        const signature = request.headers.get('x-twilio-signature');
        const isValid = validateTwilioSignature(
            process.env.TWILIO_AUTH_TOKEN!,
            signature!,
            process.env.NEXT_PUBLIC_WEBHOOK_URL!,
            payload
        );
        
        if (!isValid) {
            return new Response('Unauthorized', { status: 401 });
        }
        
        // GOTCHA: Default to demo distributor for sandbox testing
        const distributorId = process.env.DEMO_DISTRIBUTOR_ID || 'default-demo-id';
        
        // SEQUENCE: Customer -> Conversation -> Message (no transactions available)
        const phoneNumber = parsePhoneNumber(payload.From);
        const customer = await findOrCreateCustomer(phoneNumber, distributorId);
        const conversation = await findOrCreateConversation(customer.id, 'WHATSAPP', distributorId);
        const message = await createMessage({
            conversationId: conversation.id,
            content: payload.Body,
            isFromCustomer: true,
            externalMessageId: payload.MessageSid,
            externalMetadata: payload,
            distributorId
        });
        
        // CRITICAL: Return TwiML XML response (Twilio requirement)
        const twiml = new MessagingResponse();
        twiml.message('Thank you for your message! We\'ll get back to you soon.');
        
        return new Response(twiml.toString(), {
            status: 200,
            headers: { 'Content-Type': 'text/xml' }
        });
        
    } catch (error) {
        // PATTERN: Log error but return generic message for security
        console.error('Webhook processing error:', error);
        return new Response('Internal Server Error', { status: 500 });
    }
}
```

### Integration Points
```yaml
DATABASE:
  - leverage: "conversations table with channel='WHATSAPP'"
  - leverage: "messages table with external_message_id for Twilio MessageSid"
  - leverage: "webhook_endpoints table for Twilio configuration storage"
  - leverage: "webhook_deliveries table for delivery attempt logging"
  
CONFIG:
  - add to: ".env.local"
  - pattern: "TWILIO_AUTH_TOKEN=your_token_here"
  - security: "Never commit real tokens - use .env.example with placeholders"
  
COMPONENTS:
  - extend: "app/messages/hooks/useMessages.ts with WhatsApp channel support"
  - preserve: "Existing polling pattern and real-time subscription logic"
  - maintain: "Current MessageThread.tsx styling and interaction patterns"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
npm run lint                         # ESLint + Prettier for TypeScript
npm run type-check                   # TypeScript compilation check

# Expected: No errors. If errors, READ the error message and fix.
```

### Level 2: Unit Tests
```typescript
// CREATE tests/api/twilio-webhook.test.ts
import { POST } from '@/app/api/webhooks/twilio/route';

describe('Twilio Webhook Handler', () => {
  test('processes valid webhook payload', async () => {
    const mockPayload = new FormData();
    mockPayload.set('From', 'whatsapp:+1234567890');
    mockPayload.set('To', 'whatsapp:+14155238886');
    mockPayload.set('Body', 'Hello from customer');
    mockPayload.set('MessageSid', 'SM1234567890');
    
    const request = new Request('http://localhost:3000/api/webhooks/twilio', {
      method: 'POST',
      body: mockPayload,
      headers: {
        'x-twilio-signature': 'valid-signature-hash'
      }
    });
    
    const response = await POST(request);
    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toBe('text/xml');
  });

  test('rejects invalid signature', async () => {
    const request = new Request('http://localhost:3000/api/webhooks/twilio', {
      method: 'POST',
      body: new FormData(),
      headers: {
        'x-twilio-signature': 'invalid-signature'
      }
    });
    
    const response = await POST(request);
    expect(response.status).toBe(401);
  });

  test('handles missing required fields gracefully', async () => {
    const incompletePayload = new FormData();
    incompletePayload.set('From', 'whatsapp:+1234567890');
    // Missing Body, MessageSid, etc.
    
    const response = await POST(new Request('http://localhost', {
      method: 'POST',
      body: incompletePayload
    }));
    
    expect(response.status).toBe(500);
  });
});
```

```bash
# Run and iterate until passing:
npm test tests/api/twilio-webhook.test.ts
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start development server
npm run dev

# Use ngrok to expose local server (required for Twilio webhooks)
ngrok http 3000
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)

# Configure Twilio Sandbox webhook URL in console:
# https://abc123.ngrok.io/api/webhooks/twilio

# Test by sending WhatsApp message to Twilio Sandbox number
# Expected: Message appears in Messages page within 2 seconds
# Check browser Network tab for polling requests
# Check server logs for webhook processing

# Manual verification checklist:
curl -X POST http://localhost:3000/api/webhooks/twilio \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "x-twilio-signature: test-signature" \
  -d "From=whatsapp%3A%2B1234567890&To=whatsapp%3A%2B14155238886&Body=Test%20Message&MessageSid=SM123"

# Expected: 200 response with TwiML XML content
```

## Final Validation Checklist
- [ ] All tests pass: `npm test`
- [ ] No linting errors: `npm run lint`
- [ ] No type errors: `npm run type-check`
- [ ] Webhook responds with valid TwiML: `curl test above returns XML`
- [ ] Messages appear in UI within 2 seconds of webhook
- [ ] New customers created automatically from unknown numbers
- [ ] Multi-tenant isolation working (all data has correct distributor_id)
- [ ] Twilio signature validation prevents unauthorized requests
- [ ] Error cases handled gracefully with proper HTTP status codes
- [ ] Environment variables documented in .env.example
- [ ] README updated with setup and testing instructions

---

## Anti-Patterns to Avoid
- ❌ Don't implement custom Twilio signature validation - use their library
- ❌ Don't skip distributor_id filtering - multi-tenancy is critical
- ❌ Don't use database transactions - Supabase doesn't support them client-side
- ❌ Don't return JSON from webhook handler - Twilio expects TwiML XML
- ❌ Don't store raw phone numbers - always parse "whatsapp:" prefix
- ❌ Don't ignore webhook signature validation - security is mandatory
- ❌ Don't change existing polling intervals without updating requirements
- ❌ Don't hardcode distributor IDs - use environment variables for demo
- ❌ Don't create new error handling patterns - follow existing CustomerError approach