# INITIAL.md – WhatsApp Sandbox Integration (Reddi)

<!--
This file kicks off the first feature slice for the WhatsApp demo.
Only the Twilio Sandbox integration and basic Messages pipeline will be built in this PR.
-->

## Feature

**WhatsApp Sandbox Messaging (Demo)**

Build a pipeline to let demo customers send a WhatsApp message to the Twilio Sandbox number, receive that message via a webhook, store it in Supabase, and surface it in the **Messages** page of Reddi.

User goals (for demo flow):

1. **Inbound message** – Customer sends “Hola” or “quiero pedir 3 panes y 3 carnes” to the Twilio Sandbox number (they must first `join <keyword>` to register).
2. **Webhook reception** – Reddi receives the message via a POST webhook from Twilio.
3. **Data persistence** – Store each message in the `conversations` and `messages` tables (see @documentation/database/database-schema-guide.md). Create customer records in `customers` table for new phone numbers.
4. **UI update** – The Messages page displays the incoming message in real time (or via polling) as a new chat thread using existing `/app/messages/components/MessageThread.tsx` component.

### Functional spec

| Element | Details |
| --- | --- |
| WhatsApp Sandbox | Use Twilio Sandbox (no Meta verification needed). Customer must send `join <keyword>` first. |
| Webhook endpoint | Create `/app/api/whatsapp/incoming/route.ts` that Twilio calls on new messages. Parse `From`, `Body`, `MessageSid`, `Timestamp` and map to database schema |
| Supabase integration | Create/find customer by phone number in `customers` table. Create conversation in `conversations` table (channel='WHATSAPP'). Insert message in `messages` table with proper distributor_id isolation. |
| Messages page behavior | Fetch and display messages ordered by `created_at`. Support polling (every 2s) for demo. |
| Auto-response (optional) | Not yet. |

### Visual spec

- No design changes to Messages page – reuse current UI.
- Messages must appear as chat bubbles with correct sender name and timestamp.

## Examples (folder)

- The current slice only implements **webhook + Supabase + Messages UI**.

## Documentation (RAG Sources)

1. **Twilio WhatsApp Sandbox Docs** – https://www.twilio.com/docs/whatsapp/sandbox
2. **Supabase JS Client** – https://supabase.com/docs/reference/javascript (use existing `/lib/supabase/client.ts`)
3. **Reddi Messages Page** (existing code) – leverage existing components in `/app/messages/components/` and hooks in `/app/messages/hooks/`.

## Other Considerations / Gotchas

- **Twilio Sandbox registration**
    - Demo participants must send `join <keyword>` before any other message.
    - Include keyword and Sandbox number in README.
- **Webhook deployment**
    - Deploy `/app/api/whatsapp/incoming/route.ts` (Next.js 14 App Router) on Vercel (publicly accessible).
    - Use Next.js environment variables in `.env.local` (`.env.example` with Twilio creds).
- **Realtime vs Polling**
    - Use polling (2-second interval) for demo simplicity.
    - Add comment `// TODO Supabase Realtime` for future.
- **Testing flow**
    - Include steps in README to test: joining Sandbox, sending a message, seeing it in Reddi.
- **Multi-tenancy & Customer Management**
    - Handle phone number to customer mapping (create new customers for unknown numbers).
    - Ensure proper `distributor_id` isolation (all data must belong to correct distributor).
    - Default to a demo distributor for sandbox testing.
- **Folder structure (obligatory)**

```
/app/api/whatsapp/incoming/route.ts    # Next.js API Route webhook handler
/lib/supabase/client.ts                # Existing Supabase client (reuse)
/app/messages/page.tsx                 # Existing Messages page (polls Supabase)
/.env.example                          # Env vars for Twilio + Supabase
/README.md                             # Setup + testing instructions
```

- **Integration with Existing AI Pipeline**
    - Messages stored in database will be available for future AI processing.
    - Can leverage existing `useAIAgent.ts` hook for message analysis (future enhancement).
- **Lint / Format**
    - Follow ESLint + Prettier (TypeScript/React) rules already in repo.
    - Add newline at end of file for proper formatting.