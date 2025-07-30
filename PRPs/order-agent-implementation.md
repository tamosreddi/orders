name: "Order Agent - AI-Powered Message Processing and Order Management"
description: |

## Purpose
Build a production-ready Pydantic AI agent that automatically processes customer messages from multiple channels (WhatsApp, SMS, email), classifies intent, extracts order details, validates products, and inserts orders into the database with proper workflow management.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a complete Order Agent system that processes customer messages and automatically handles order-related tasks through a 6-step workflow:
1. Read and analyze customer messages from database
2. Classify intent with confidence scoring
3. Extract order details for "Buy" intents (handling multi-message orders)
4. Validate products against catalog
5. Insert orders into database with "Pendiente" status
6. Enable human review and confirmation through order management interface

## Why
- **Business value**: Automates 80%+ of order processing tasks currently done manually by sales reps
- **Integration**: Seamlessly works with existing Next.js frontend and Supabase database
- **Problems solved**: Eliminates manual copying of WhatsApp orders to ERP, reduces errors, enables 24/7 order processing, improves customer response times
- **Scalability**: Can process hundreds of messages per hour with consistent accuracy

## What
A Python-based AI agent system that:
- Monitors the `messages` table for unprocessed customer messages
- Uses OpenAI API to classify intent and extract structured order data
- Validates products against the existing product catalog
- Creates orders in the `orders` and `order_products` tables
- Provides confidence scoring and human review mechanisms
- Integrates with the existing Next.js order management interface

### Success Criteria
- [ ] Agent successfully processes messages and classifies intent with >90% accuracy
- [ ] Order extraction captures all product details from natural language messages
- [ ] Product validation matches customer requests to catalog items with fuzzy matching
- [ ] Orders are created in database with proper status workflow ("Pendiente" → "En Revisión" → "Confirmada")
- [ ] Human review interface displays extracted orders with edit capabilities
- [ ] System handles multi-message orders and order corrections gracefully
- [ ] All tests pass and code meets quality standards (ruff, mypy, pytest)
- [ ] Agent processes messages in under 30 seconds with proper error handling

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/agents/
  why: Core agent creation patterns and dependency injection
  
- url: https://ai.pydantic.dev/tools/
  why: Function tools registration and context management
  
- url: https://ai.pydantic.dev/dependencies/
  why: Dependency injection system for database connections
  
- url: https://supabase.com/docs/reference/python/introduction
  why: Python client for database operations and authentication
  
- url: https://supabase.com/docs/guides/ai
  why: AI integration patterns and vector database capabilities

  - url: https://platform.openai.com/docs/api-reference/responses
  why: OpenAI main API to build AI agents.
  
- file: examples/example_pydantic_ai.py
  why: Dependency injection pattern, tool registration, Supabase integration, async patterns
  
- file: examples/example_pydantic_ai_mcp.py
  why: Environment variable handling, streaming responses, CLI patterns
  
- file: documentation/database/database-schema-guide.md
  why: Complete database schema with AI-enhanced tables and relationships
  
- file: documentation/database/database-relationships-diagram.md
  why: Data flow patterns and table relationships for order processing

- file: lib/supabase/client.ts
  why: Existing Supabase connection patterns (for reference, will adapt to Python)
  
- file: tests/orders.test.tsx
  why: Testing patterns and validation approaches for order-related functionality
```

### Current Codebase tree
```bash
/Users/macbook/orderagent/
├── app/                          # Next.js frontend
│   ├── orders/                   # Order management pages
│   ├── messages/                 # Message management pages
│   └── api/
├── components/                   # React components
│   ├── OrderReview/              # Order review components
│   └── OrderTable.tsx
├── lib/
│   ├── supabase/                 # TypeScript Supabase client
│   └── utils/
├── documentation/
│   ├── database/                 # Database schema documentation
│   └── agents/                   # Agent architecture docs
├── examples/
│   ├── example_pydantic_ai.py    # Pydantic AI patterns
│   └── example_pydantic_ai_mcp.py # MCP integration patterns
├── supabase/
│   └── migrations/               # Database schema migrations
├── tests/                        # TypeScript/React tests
└── .env                          # Environment variables
```

### Desired Codebase tree with files to be added
```bash
/Users/macbook/orderagent/
├── agents/                       # Order Agent logic and instructions
│   ├── __init__.py
│   ├── order_agent.py           # Main agent with intent, parsing, tools
│   ├── prompts.py               # System prompts and templates
│   └── tools.py                 # Agent tools (database, validation)
├── schemas/                      # Pydantic models for structured outputs
│   ├── __init__.py
│   ├── order.py                 # Order, OrderItem, AgentResult schemas
│   ├── message.py               # Message processing schemas
│   └── product.py               # Product matching schemas
├── tools/                        # External actions/tools agent can call
│   ├── __init__.py
│   ├── supabase_tools.py        # create_order, fetch_catalog, message processing
│   ├── product_matcher.py       # Fuzzy product matching logic
│   └── intent_classifier.py     # Intent classification utilities
├── services/                     # Core services, not tied to AI logic
│   ├── __init__.py
│   ├── database.py              # Supabase client setup and helpers
│   ├── message_processor.py     # Message processing service
│   └── order_manager.py         # Order lifecycle management
├── config/                       # Environment and settings
│   ├── __init__.py
│   └── settings.py              # API keys, Supabase URL configuration
├── tests/                        # Python unit tests
│   ├── __init__.py
│   ├── test_order_agent.py      # Agent functionality tests
│   ├── test_message_processing.py # Message processing tests
│   ├── test_product_matching.py # Product validation tests
│   └── test_database_integration.py # Database operation tests
├── main.py                       # Entry point (runs the Order Agent)
├── requirements.txt              # Python dependencies
└── README.md                     # Documentation
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Pydantic AI requires async throughout - no sync functions in async context
# CRITICAL: Always use dependency injection pattern for database connections
# CRITICAL: Supabase Python client requires proper connection pooling for production
# CRITICAL: OpenAI API has rate limits - implement proper retry logic with exponential backoff
# CRITICAL: Messages can be processed out of order - use proper sequencing logic
# CRITICAL: Multi-tenant database - ALWAYS filter by distributor_id in queries
# CRITICAL: AI confidence scores must be stored for continuous improvement
# CRITICAL: Use RLS policies - they automatically enforce tenant isolation
# CRITICAL: JSON fields in Supabase require proper serialization/deserialization
# CRITICAL: Virtual environment 'venv_linux' must be used for all Python execution
# CRITICAL: Large messages may exceed token limits - implement chunking strategy
# CRITICAL: Database transactions required for order creation (order + order_products)
```

## Implementation Blueprint

### Data models and structure

```python
# schemas/message.py - Message processing models
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class MessageIntent(BaseModel):
    intent: Literal["BUY", "QUESTION", "COMPLAINT", "FOLLOW_UP", "OTHER"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Why this intent was chosen")

class ExtractedProduct(BaseModel):
    product_name: str = Field(..., description="Product name as mentioned by customer")
    quantity: int = Field(..., ge=1, description="Quantity requested")
    unit: Optional[str] = Field(None, description="Unit mentioned (bottles, cases, kg)")
    original_text: str = Field(..., description="Original text that mentioned this product")
    confidence: float = Field(..., ge=0.0, le=1.0)

class MessageAnalysis(BaseModel):
    message_id: str
    intent: MessageIntent
    extracted_products: List[ExtractedProduct] = []
    customer_notes: Optional[str] = None
    delivery_date: Optional[str] = None
    processing_time_ms: int

# schemas/order.py - Order creation models
class OrderProduct(BaseModel):
    product_name: str
    quantity: int
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    line_price: Optional[float] = None
    ai_confidence: float
    original_text: str
    matched_product_id: Optional[str] = None
    matching_confidence: Optional[float] = None

class OrderCreation(BaseModel):
    customer_id: str
    distributor_id: str
    conversation_id: Optional[str] = None
    channel: Literal["WHATSAPP", "SMS", "EMAIL"]
    products: List[OrderProduct]
    delivery_date: Optional[str] = None
    additional_comment: Optional[str] = None
    ai_confidence: float
    source_message_ids: List[str]

# schemas/product.py - Product matching models
class ProductMatch(BaseModel):
    product_id: str
    product_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    match_type: Literal["EXACT", "FUZZY", "ALIAS", "AI_ENHANCED"]
    match_score: float = Field(..., ge=0.0, le=1.0)
```

### List of tasks to be completed to fulfill the PRP in the order they should be completed

```yaml
Task 1: Setup Project Foundation and Configuration
CREATE config/settings.py:
  - PATTERN: Use python-dotenv like examples/example_pydantic_ai.py
  - Load environment variables from existing .env file
  - Validate required keys (OPENAI_API_KEY, SUPABASE_PROJECT_URL, SUPABASE_API_KEY)
  - Create Pydantic settings model with proper types

CREATE services/database.py:
  - PATTERN: Mirror examples/example_pydantic_ai.py Supabase client setup
  - Create async Supabase client with connection pooling
  - Implement get_current_distributor_id() function for multi-tenancy
  - Add helper functions for common database operations

Task 2: Implement Core Pydantic Models and Schemas
CREATE schemas/message.py:
  - PATTERN: Use pydantic BaseModel like examples
  - Implement MessageIntent, ExtractedProduct, MessageAnalysis models
  - Add proper validation and field descriptions for AI context
  - Include confidence scoring fields for all AI outputs

CREATE schemas/order.py:
  - PATTERN: Mirror existing TypeScript order types but in Pydantic
  - Implement OrderProduct, OrderCreation models
  - Include all fields that match database order_products table structure
  - Add AI metadata fields (confidence, original_text, matching data)

CREATE schemas/product.py:
  - Implement ProductMatch model for catalog matching
  - Include fuzzy matching confidence and scoring fields
  - Add validation for match types and confidence ranges

Task 3: Build Database Integration Tools
CREATE tools/supabase_tools.py:
  - PATTERN: Use async functions with dependency injection like examples/example_pydantic_ai.py
  - Implement fetch_unprocessed_messages() - gets messages where ai_processed=FALSE
  - Implement update_message_ai_data() - updates ai_extracted_intent, ai_confidence, ai_processed
  - Implement create_order() - inserts order with transaction for order + order_products
  - Implement fetch_product_catalog() - gets products with aliases and keywords for matching
  - Always filter by distributor_id for multi-tenancy
  - Use database transactions for atomic operations

CREATE tools/product_matcher.py:
  - Implement fuzzy string matching using fuzzywuzzy or similar
  - Create match_products_to_catalog() function
  - Use product aliases, keywords, and AI training examples from database
  - Return ProductMatch objects with confidence scores
  - Handle common misspellings and variations

Task 4: Create the Core Order Agent
CREATE agents/prompts.py:
  - Define system prompt for intent classification
  - Define system prompt for order extraction
  - Include context about the business (B2B distributor, product types)
  - Provide examples of good intent classification and order extraction
  - Include instructions for confidence scoring

CREATE agents/order_agent.py:
  - PATTERN: Follow examples/example_pydantic_ai.py structure with Agent, deps_type, tools
  - Create OrderAgentDeps dataclass with Supabase client and settings
  - Initialize Agent with OpenAI model and system prompt
  - Register tools: analyze_message_intent, extract_order_details, validate_products
  - Implement main process_message() method that orchestrates the 6-step workflow
  - Include proper error handling and retry logic with ModelRetry
  - Use async/await throughout

Task 5: Implement Agent Tools and Workflow
CREATE agents/tools.py:
  - PATTERN: Use @agent.tool decorator like examples/example_pydantic_ai.py
  - Implement analyze_message_intent() tool - returns MessageIntent
  - Implement extract_order_details() tool - returns List[ExtractedProduct] 
  - Implement validate_and_match_products() tool - matches to catalog
  - Implement create_order_from_extraction() tool - creates database order
  - All tools should use RunContext[OrderAgentDeps] for database access
  - Include proper confidence scoring and error handling

Task 6: Create Message Processing Service
CREATE services/message_processor.py:
  - Implement MessageProcessor class with async methods
  - Create process_pending_messages() - main loop for processing unprocessed messages
  - Handle multi-message order scenarios (customer edits, additions)
  - Implement order consolidation logic for related messages
  - Add proper logging and error handling
  - Respect AI confidence threshold from distributor settings

CREATE services/order_manager.py:
  - Implement OrderManager class for order lifecycle management
  - Create methods for order status transitions (Pendiente → En Revisión → Confirmada)
  - Handle order validation and confirmation workflow
  - Integrate with existing frontend order review system
  - Add order update and modification capabilities

Task 7: Build Main Application Entry Point
CREATE main.py:
  - PATTERN: Use asyncio.run() like examples/example_pydantic_ai_mcp.py
  - Initialize OrderAgent with proper dependencies
  - Create main processing loop that checks for new messages
  - Add graceful shutdown handling and signal processing
  - Include comprehensive logging setup
  - Add health check endpoint if needed for monitoring

Task 8: Implement Comprehensive Testing Suite
CREATE tests/test_order_agent.py:
  - PATTERN: Use pytest with async test patterns
  - Mock external API calls (OpenAI, Supabase)
  - Test intent classification accuracy with various message types
  - Test order extraction with different product formats
  - Test confidence scoring and threshold handling
  - Test error handling and retry logic

CREATE tests/test_message_processing.py:
  - Test multi-message order scenarios
  - Test order consolidation and customer corrections
  - Test different message channels (WhatsApp, SMS, Email)
  - Test edge cases (empty messages, very long messages)

CREATE tests/test_product_matching.py:
  - Test fuzzy matching accuracy with various product names
  - Test handling of misspellings and alternative names
  - Test matching confidence scoring
  - Test catalog product alias and keyword matching

CREATE tests/test_database_integration.py:
  - Test Supabase client connection and queries  
  - Test multi-tenant data isolation (distributor_id filtering)
  - Test transaction handling for order creation
  - Test proper RLS policy enforcement

Task 9: Add Production Configurations and Documentation
UPDATE requirements.txt:
  - Add all required dependencies with pinned versions
  - Include: pydantic-ai, openai, supabase, python-dotenv, fuzzywuzzy, pytest, ruff, mypy

CREATE README.md:
  - Document setup and installation instructions
  - Explain the 6-step order processing workflow
  - Provide examples of message formats and expected outputs
  - Include troubleshooting guide and monitoring recommendations
  - Document configuration options and environment variables

Task 10: Integration with Existing Frontend
MODIFY existing order management pages:
  - Ensure order review interface can display AI-generated orders
  - Add confidence score display for AI-extracted data
  - Enable editing of AI-extracted product information
  - Add proper status transitions (Pendiente → En Revisión → Confirmada)
  - Test end-to-end workflow from message to confirmed order
```

### Per task pseudocode

```python
# Task 4: Core Order Agent Structure
@dataclass
class OrderAgentDeps:
    supabase: Client
    settings: Settings
    
system_prompt = """
You are an expert order processing agent for a food B2B distributor.
Your job is to analyze customer messages and extract order details accurately.

Key responsibilities:
1. Classify customer intent (BUY, QUESTION, COMPLAINT, FOLLOW_UP, OTHER)
2. For BUY intents, extract product names, quantities, and units
3. Provide confidence scores for all extractions
4. Handle multi-message orders and customer corrections

Always be conservative with confidence scores. If uncertain, provide lower confidence.
"""

order_agent = Agent(
    model=OpenAIModel('gpt-4'),
    system_prompt=system_prompt,
    deps_type=OrderAgentDeps,
    retries=2
)

@order_agent.tool
async def analyze_message_intent(ctx: RunContext[OrderAgentDeps], message_content: str) -> MessageIntent:
    # PATTERN: Use structured response validation like examples
    # CRITICAL: Return confidence score between 0.0 and 1.0
    # GOTCHA: Handle edge cases like empty messages or emoji-only messages
    pass

# Task 6: Message Processing Service  
class MessageProcessor:
    def __init__(self, agent: Agent, supabase: Client):
        self.agent = agent
        self.supabase = supabase
    
    async def process_pending_messages(self, distributor_id: str) -> List[ProcessingResult]:
        # PATTERN: Use database transactions for atomic operations
        async with self.supabase.transaction():
            # CRITICAL: Always filter by distributor_id for multi-tenancy
            messages = await self.supabase.from_('messages') \
                .select('*') \
                .eq('ai_processed', False) \
                .eq('distributor_id', distributor_id) \
                .order('created_at') \
                .execute()
            
            results = []
            for message in messages.data:
                # GOTCHA: Handle rate limits with proper backoff
                try:
                    result = await self.agent.run(
                        f"Process this customer message: {message.content}",
                        deps=OrderAgentDeps(supabase=self.supabase, settings=self.settings)
                    )
                    
                    # CRITICAL: Update ai_processed flag and extracted data
                    await self._update_message_analysis(message.id, result.data)
                    results.append(result)
                    
                except ModelRetry as e:
                    # PATTERN: Retry with exponential backoff
                    await asyncio.sleep(min(2 ** attempt, 60))
                    continue
                    
        return results

# Task 3: Database Integration
async def create_order(
    ctx: RunContext[OrderAgentDeps], 
    order_data: OrderCreation
) -> str:
    # CRITICAL: Use transaction for order + order_products creation
    async with ctx.deps.supabase.transaction():
        # PATTERN: Insert order record first
        order_result = await ctx.deps.supabase.from_('orders').insert({
            'customer_id': order_data.customer_id,
            'distributor_id': order_data.distributor_id,
            'status': 'PENDIENTE',  # Spanish as specified in requirements
            'ai_generated': True,
            'ai_confidence': order_data.ai_confidence,
            'channel': order_data.channel,
            # ... other fields
        }).execute()
        
        order_id = order_result.data[0]['id']
        
        # PATTERN: Insert order products as separate records
        products_to_insert = []
        for product in order_data.products:
            products_to_insert.append({
                'order_id': order_id,
                'product_name': product.product_name,
                'quantity': product.quantity,
                'ai_extracted': True,
                'ai_confidence': product.ai_confidence,
                'ai_original_text': product.original_text,
                # ... other fields
            })
        
        await ctx.deps.supabase.from_('order_products').insert(products_to_insert).execute()
        return order_id
```

### Integration Points
```yaml
DATABASE:
  - tables: messages, orders, order_products, products, customers, conversations
  - indexes: "Ensure distributor_id indexes exist for performance"
  - constraints: "Foreign key constraints for data integrity"
  
CONFIG:
  - environment: Use existing .env file with all required variables
  - settings: "OPENAI_API_KEY, SUPABASE_PROJECT_URL, SUPABASE_API_KEY"
  - distributor: "AI_CONFIDENCE_THRESHOLD per distributor for auto-processing"
  
FRONTEND:
  - integration: Order management pages in app/orders/
  - display: Show AI confidence scores and extracted data
  - editing: Allow human review and correction of AI extractions
  - workflow: Support status transitions (Pendiente → En Revisión → Confirmada)
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check . --fix              # Auto-fix style issues
mypy .                          # Type checking

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# tests/test_order_agent.py
async def test_intent_classification_accuracy():
    """Test agent correctly classifies different message types"""
    agent = create_test_agent()
    
    # Test buy intent
    result = await agent.run("I need 5 bottles of milk and 2 cases of beer")
    assert result.data.intent.intent == "BUY"
    assert result.data.intent.confidence > 0.8
    
    # Test question intent  
    result = await agent.run("What's the price of your milk?")
    assert result.data.intent.intent == "QUESTION"
    
    # Test complaint intent
    result = await agent.run("The last delivery was late and the milk was warm")
    assert result.data.intent.intent == "COMPLAINT"

async def test_order_extraction_accuracy():
    """Test agent extracts products correctly from natural language"""
    agent = create_test_agent()
    result = await agent.run("I want 10 bottles of coca cola and 5 kg of cheese")
    
    assert len(result.data.extracted_products) == 2
    
    products = result.data.extracted_products
    assert products[0].product_name in ["coca cola", "Coca Cola"]
    assert products[0].quantity == 10
    assert products[1].quantity == 5
    assert products[1].unit == "kg"

def test_multi_message_order_consolidation():
    """Test handling of orders spread across multiple messages"""
    processor = MessageProcessor(agent, supabase_client)
    
    messages = [
        "I need milk",
        "Make it 5 bottles", 
        "Also add 2 cases of beer"
    ]
    
    # Process messages in sequence
    results = []
    for msg in messages:
        result = processor.process_message(msg, customer_id="test123")
        results.append(result)
    
    # Final result should have consolidated order
    final_order = results[-1].extracted_products
    assert len(final_order) == 2
    assert any(p.product_name == "milk" and p.quantity == 5 for p in final_order)
    assert any(p.product_name == "beer" and p.quantity == 2 for p in final_order)

def test_product_catalog_matching():
    """Test fuzzy matching against product catalog"""
    matcher = ProductMatcher(product_catalog)
    
    # Test exact match
    match = matcher.match_product("Whole Milk 1L")
    assert match.match_type == "EXACT"
    assert match.confidence == 1.0
    
    # Test fuzzy match
    match = matcher.match_product("whole milk")
    assert match.match_type == "FUZZY"
    assert match.confidence > 0.7
    
    # Test alias match
    match = matcher.match_product("leche")  # Spanish for milk
    assert match.match_type == "ALIAS"
    assert match.confidence > 0.8
```

```bash
# Run tests iteratively until passing:
uv run pytest tests/ -v --cov=agents --cov=tools --cov=services --cov-report=term-missing

# If failing: Debug specific test, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test the complete workflow end-to-end
python main.py --test-mode

# Expected workflow:
# 1. Agent processes test messages from database
# 2. Intent classification works correctly  
# 3. Order extraction captures all products
# 4. Products are matched to catalog
# 5. Orders are created in database with proper status
# 6. Frontend can display and edit the orders

# Check database for created orders:
# SELECT * FROM orders WHERE ai_generated = true ORDER BY created_at DESC LIMIT 5;
# SELECT * FROM order_products WHERE order_id IN (SELECT id FROM orders WHERE ai_generated = true);

# Test message processing:
curl -X POST http://localhost:8000/process-messages \
  -H "Content-Type: application/json" \
  -d '{"distributor_id": "test-distributor-id"}'

# Expected: {"processed": 3, "orders_created": 1, "avg_confidence": 0.85}
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `ruff check .`
- [ ] No type errors: `mypy .`
- [ ] Agent processes messages and classifies intent accurately
- [ ] Order extraction works for various message formats
- [ ] Product matching handles fuzzy names and misspellings
- [ ] Orders are created in database with proper multi-tenancy
- [ ] Frontend displays AI-generated orders correctly
- [ ] Human review workflow functions properly
- [ ] Multi-message orders are consolidated correctly
- [ ] Error cases handled gracefully with proper logging
- [ ] Performance meets requirements (<30s per message)

---

## Anti-Patterns to Avoid
- ❌ Don't ignore distributor_id filtering - breaks multi-tenancy
- ❌ Don't use sync functions in async agent context
- ❌ Don't skip confidence scoring - needed for continuous improvement
- ❌ Don't hardcode prompts - use configurable prompt templates
- ❌ Don't ignore rate limits - implement proper backoff strategies
- ❌ Don't create orders without transactions - can leave partial data
- ❌ Don't assume single-message orders - customers often send multiple messages
- ❌ Don't ignore existing order statuses - follow the specified workflow

## Confidence Score: 9/10

High confidence due to:
- Clear database schema with AI-enhanced fields already in place
- Existing Pydantic AI examples demonstrating proper patterns
- Well-defined 6-step workflow with specific requirements
- Comprehensive database documentation and relationships
- Proven Supabase integration patterns in codebase
- Clear validation gates and testing approaches

Minor uncertainty on:
- Exact fuzzy matching algorithms for product catalog (will need fine-tuning)
- Multi-message order consolidation logic complexity (may need iterative refinement)
- OpenAI API rate limiting behavior under high load (monitoring needed)