## FEATURE:

- **Autonomous AI Agent** that processes customer messages and makes intelligent decisions about order processing without following fixed rules.
- **Goal-oriented decision making** where the agent evaluates multiple possible actions against business goals (customer satisfaction, order value, efficiency).
- **Context-aware processing** that adapts responses based on customer history, preferences, urgency, and inventory status.
- **Proactive assistance** that suggests alternatives, asks clarifying questions, and anticipates customer needs.
- **Learning and adaptation** from conversation outcomes to improve future interactions.
- **Supabase integration** for data persistence and OpenAI API for autonomous reasoning and decision making.

## BUSINESS VALUE:

- **Revenue Impact**: Target 15-25% increase in average order value through intelligent upselling and proactive suggestions
- **Efficiency Gains**: Reduce manual order processing time by 60-80% (similar to YC success stories like Yuma)
- **Customer Experience**: Improve satisfaction scores through personalized, context-aware interactions
- **Scalability**: Handle unlimited concurrent conversations with consistent quality

## AUTONOMOUS AGENT CAPABILITIES:

### **Intelligent Decision Making:**
- **Dynamic action selection** instead of fixed if/else logic
- **Goal evaluation** against multiple business objectives
- **Context-aware reasoning** considering customer history, preferences, and situation
- **Proactive suggestions** based on customer behavior patterns

### **Available Actions (Functions):**
- `create_order`: Create new order with extracted products and customer preferences
- `ask_clarification`: Ask contextual questions when information is unclear
- `suggest_alternatives`: Recommend alternative products when requested items unavailable
- `check_inventory`: Verify product availability and suggest substitutes
- `escalate_to_human`: Transfer complex cases to human agent
- `send_catalog`: Provide relevant product information
- `confirm_order_details`: Summarize order and ask for confirmation
- `handle_complaint`: Process customer complaints and offer solutions

### **Business Goals:**
- **Customer Satisfaction** (weight: 0.4): Ensure positive customer experience
- **Order Value** (weight: 0.3): Maximize revenue per order
- **Efficiency** (weight: 0.2): Reduce processing time and errors
- **Relationship Building** (weight: 0.1): Foster long-term customer relationships

## EXAMPLES:

In the `examples/` folder, there are Pydantic AI implementation examples to guide the Autonomous Order Agent development:

- `examples/example_pydantic_ai.py` - Demonstrates Pydantic AI agent with tools, dependencies injection pattern using PydanticAIDeps dataclass, Supabase integration, and proper async/await patterns for AI agent development.
- `examples/example_pydantic_ai_mcp.py` - Shows MCP (Model Context Protocol) integration with Pydantic AI, including proper environment variable handling, streaming responses, and CLI chat interface patterns.

Use these examples as templates for agent architecture, dependency management, tool registration, and async patterns. The dependency injection pattern from example_pydantic_ai.py is particularly relevant for the Autonomous Order Agent's Supabase integration.

## DOCUMENTATION:

Pydantic AI documentation: https://ai.pydantic.dev/
Supabase Python client: https://supabase.com/docs/reference/python/introduction
OpenAI API documentation: https://platform.openai.com/docs/api-reference
For Supabase Database structure and information: /documentation/database

## PROJECT STRUCTURE:

```
project_root/
├── agents/                          # Autonomous Agent logic and instructions
│   ├── autonomous_order_agent.py    # Main autonomous agent with goal-oriented decision making
│   ├── order_agent.py               # Current rule-based agent (for comparison/fallback)
│   ├── agent_factory.py             # Factory to choose between agents
│   └── __init__.py
├── schemas/                         # Pydantic models for structured outputs
│   ├── order.py                     # Order, OrderItem, AgentResult schemas
│   ├── autonomous_agent.py          # Autonomous agent specific schemas
│   ├── goals.py                     # Business goals and constraints
│   └── __init__.py
├── tools/                           # External actions/tools agent can call
│   ├── supabase_tools.py            # create_order, fetch_catalog, etc.
│   ├── autonomous_actions.py        # Autonomous agent specific actions
│   └── __init__.py
├── services/                        # Core services, not tied to AI logic
│   ├── database.py                  # Supabase client setup and helpers
│   ├── message_ingest.py            # Message processing from database
│   ├── conversation_memory.py       # Memory system for autonomous agent
│   ├── goal_evaluator.py            # Evaluate actions against business goals
│   └── __init__.py
├── config/                          # Environment and settings
│   ├── settings.py                  # API keys, Supabase URL configuration
│   ├── feature_flags.py             # Feature flags for agent switching
│   └── __init__.py
├── main.py                          # Entry point (runs the Autonomous Order Agent)
├── requirements.txt                 # Dependencies (pydantic-ai, supabase, etc.)
└── README.md
```

## AUTONOMOUS AGENT WORKFLOW:

### **1. Message Reception and Context Building**
- Receive customer message from webhook
- Build comprehensive context including:
  - Customer history and preferences
  - Recent orders and interactions
  - Current inventory status
  - Time of day and urgency indicators
  - Conversation memory and previous decisions

### **2. Autonomous Decision Making**
- Use OpenAI function calling to evaluate all possible actions
- Consider business goals and constraints
- Generate multiple action options
- Evaluate each action against goals (satisfaction, value, efficiency, relationship)
- Select optimal action based on weighted scoring

### **3. Action Execution and Learning**
- Execute the chosen action
- Monitor customer response and satisfaction
- Learn from outcomes to improve future decisions
- Update conversation memory and customer profiles

### **4. Proactive Assistance**
- Anticipate customer needs based on patterns
- Suggest relevant products or alternatives
- Ask clarifying questions when information is unclear
- Offer upsell opportunities when appropriate


## FEATURE FLAGS AND ROLLOUT:

### **Environment Variables:**
```bash
# .env file
USE_AUTONOMOUS_AGENT=false                    # Master switch
AUTONOMOUS_AGENT_PERCENTAGE=0                 # Percentage of messages to process
AUTONOMOUS_AGENT_GOALS_ENABLED=true           # Enable goal evaluation
AUTONOMOUS_AGENT_LEARNING_ENABLED=false       # Enable learning from outcomes
AUTONOMOUS_AGENT_PROACTIVE_ENABLED=false      # Enable proactive suggestions
```


## AUTONOMOUS AGENT SCHEMAS:

### **Business Goals Schema:**
```python
class BusinessGoal:
    name: str                    # Goal name (e.g., "customer_satisfaction")
    weight: float               # Importance weight (0.0 to 1.0)
    description: str            # Goal description
    metrics: List[str]          # How to measure success
```

### **Action Evaluation Schema:**
```python
class ActionEvaluation:
    action_name: str            # Name of the action
    goal_scores: Dict[str, float]  # Score for each business goal
    overall_score: float        # Weighted overall score
    reasoning: str              # Why this action was chosen
    confidence: float           # Confidence in the decision
```

### **Conversation Memory Schema:**
```python
class ConversationMemory:
    customer_id: str            # Customer identifier
    conversation_history: List[Dict]  # Previous messages and decisions
    customer_preferences: Dict  # Learned preferences
    successful_patterns: Dict   # Patterns that worked well
    last_interaction: datetime  # Last interaction timestamp
```

## TESTING AND MONITORING:

### **Performance Metrics:**
- **Processing Time**: Average time to process messages
- **Customer Satisfaction**: Response quality and helpfulness
- **Order Value**: Average order value and conversion rate
- **Error Rate**: Failed decisions and fallback frequency
- **Learning Effectiveness**: Improvement over time

### **Monitoring Dashboard:**
- Real-time performance comparison
- Decision quality metrics
- Learning progress tracking
- Error rate monitoring

## OTHER CONSIDERATIONS:

- Use the existing .env file which already contains all required environment variables (OPENAI_API_KEY, SUPABASE_PROJECT_URL, SUPABASE_API_KEY, etc.)
- Use the existing table structure and think how to use the existing columns
- Include the project structure in the README following the infrastructure outlined in pre-initial.md
- Virtual environment `venv_linux` has already been set up with the necessary dependencies
- Use python_dotenv and load_env() for environment variables
- Keep files under 500 lines of code each, split into logical modules
- Create comprehensive Pytest unit tests for all functionality
- Use type hints throughout and follow PEP8 standards
- Ensure robust error handling and logging throughout the system
- Database integration should work with existing tables structure for messages, orders, order_products, and other existing tables
- Be simple and practical, don't over complicate and look for the smart secure route
- **Zero-risk deployment**: Autonomous agent runs parallel to current system
- **Easy rollback**: Switch back to current system instantly via feature flag
- **Gradual migration**: Move traffic slowly from current to autonomous system
- **Performance comparison**: Monitor both systems side by side
- **Learning from outcomes**: Improve decisions based on customer responses 