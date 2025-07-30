**What is it:** The Order_Agent is an AI-powered assistant. Its primary job is to process every incoming customer message (received via WhatsApp, email, or other channels) and automatically handle sales-related tasks that sales reps currently do manually.

**Why This Agent Exists:** This agent automates the entire order-handling workflow, freeing salespeople from repetitive tasks like manually copying orders from WhatsApp into the ERP, validating product details, and sending confirmations. It ensures orders are processed faster, more accurately, and at scale, while still escalating edge cases to human staff when needed.

**Infrastructure:** This is the typical folder structure: (Let´s just build for the Order Agent.

```jsx
project_root/
│
├── agents/                      # Each AI agent lives here (logic + instructions)
│   ├── order_agent.py           # Handles intent, parsing, Supabase + ERP tools
│   ├── lead_scoring_agent.py    # (Future) Scores customers for upsells
│   ├── insights_agent.py        # (Future) Sales insights and analytics
│   └── __init__.py
│
├── schemas/                     # Pydantic models for structured outputs
│   ├── order.py                 # Order, OrderItem, AgentResult schemas
│   ├── lead.py                  # (Future) Lead scoring schemas
│   └── __init__.py
│
├── tools/                       # External actions/tools agents can call
│   ├── supabase_tools.py        # create_order, fetch_catalog, etc.
│   ├── erp_tools.py             # ERP automation or API connectors
│   ├── twilio_tools.py          # Access WhatsApp messages
│   └── __init__.py
│
├── services/                    # Core services, not tied to AI logic
│   ├── database.py              # Supabase client setup and helpers
│   ├── message_ingest.py        # Fetch new messages from Twilio
│   └── __init__.py
│
├── orchestrator/                # (Later) Orchestrates multiple agents
│   ├── main.py                  # Uses Agents SDK to route tasks
│   └── __init__.py
│
├── config/                      # Environment and settings
│   ├── settings.py              # API keys, Supabase URL, ERP creds
│   └── __init__.py
│
├── main.py                      # Entry point (runs the Order Agent for now)
├── requirements.txt             # Dependencies (pydantic-ai, supabase, etc.)
└── README.md

```

### **Detailed Agent Goal (Step-by-Step Responsibilities)**

1. **Read and analyze every new customer message**
    - The agent scans each incoming WhatsApp (or similar) message that is stored in the company’s database. From the “messages” table.
    - Each message is processed individually, even if it’s part of a longer conversation, to ensure nothing is missed.
2. **Identify the customer’s intent**
    - The agent determines the purpose of the message, classifying it into one of the following intents:
        - **Buy** – The customer is trying to place an order or reorder products.
        - **Question** – The customer is asking about pricing, availability, promotions, or delivery.
        - **Complaint** – The customer has a service or product issue.
        - **Follow-up** – The customer is following up on a previous order, delivery, or payment.
        - **Other** – Any other message (e.g., casual chat, unrelated content).
    - Every message should have an intent and must be recorded in the “messages” table in the column “ai_extracted_intent”
    - The Agent also must record from a scale of 0% to 100% the confidence of that intent interpretation. This should be registered in the column “ai_confidence”.
    - When a message is analyzed for intent, then the column “ai_processed” should be TRUE.
3. **If the intent is “BUY” (order placement):**
    - **Look, find and Extract the order details** from the message(s). Your goal is to fully capture and understand what the customer wants to order. Please consider that the customer might make the order in multiple messages, or that the customer can correct himself, or edit the order. The Agent must account for that. The data collected:
        - Customer identifier (if available or inferable).
        - List of products (SKUs or descriptions).
        - Quantities for each item.
        - Requested delivery date (or default to next available).
        - Any additional notes (special instructions, discounts, etc.).
        - Any additional data that is valuable and can be extracted: date, time, etc, etc., etc.
    - The extracted data must be structured and validated according to a defined format (e.g., a JSON schema). This data should be registered in the ai_extracted_products column. But always remember that the aent must be able to recognize edits, changes, adding, reducing, form multiple messages.
4. **Validate the order information**
    - The agent checks each SKU against the company’s product catalog (stored in an external database or document).
    - The agent must be able to see the document and look for the products that are being ordered and check if the names are right, or if there i enough stock or any other related important thing.
    - If an SKU is invalid or missing, the agent flags it for review.
    - If the agent needs clarification, and is more than 90% sure about it, the agent is allows to create a short message and automatically send it to the customer JUST FOR CLARIFICATION purposes.
5. **Insert the order in the Orders Table**
    - The new order must be then inserted as a new row in the “orders” table with a “Pendiente” status. The main columns of the table in the Orders page are: Cliente, Recibida, Fecha de Envío (this is the date this order must be sent), Products, Status.
    - The goal is for the user to be able to see the order and its details.
    - The status will change to “En Revisión” once the user clicks in the row to “see” the Order Details at least once.
    - The status will change to “Confirmada” only quen the user clicks on “Aceptar Pedido” on the “En Revisión” panel that is open when an order is selected.
    - Each order is timestamped and linked to the customer for reporting and follow-up.
    - The “Order Review” panel MUST be completely filled with the information gathered form this particular order. Including the customer information. In the “Order Review” there´s a table where all the products that has been gathered from the order, from the column “ai_extracted_products” in the “messages” table must appear here. Thios information must populate and be registered in the table “order_products”.
6. **Order Confirmation**
    - The user must be able to see, review, edit, and confirm the order. These changes must be reflected in the table “order_products”
    - If the order is confirmed, then change the status to “Confirmada” and the user is taken back to the Orders page.

For the moment, that´s all. Don´t add anything else than this for the moment. 

We need to use the Pydantic Framework.

We will use Responses API from ChatGPT for the Agent.
For all this taks, it must only be one agent named Order_Agent.
Must be very very well structured and organized in terms of the code.

You must look at the documentation form the data tables to undesrtand table structure and infer and assume where each data must be saved.

Keep it simple and avoid anything that might bring lots of risks of bugs and crashes!