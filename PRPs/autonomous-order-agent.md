name: "Autonomous Order Agent PRP - Goal-Oriented Decision Making"
description: |

# Autonomous Order Agent Implementation PRP

## Goal
Build an **Autonomous AI Agent** that processes customer messages and makes intelligent decisions about order processing without following fixed rules. The agent will use goal-oriented decision making to evaluate multiple possible actions against business objectives and select optimal actions based on weighted scoring.

## Why
- **Revenue Impact**: Target 15-25% increase in average order value through intelligent upselling and proactive suggestions
- **Efficiency Gains**: Reduce manual order processing time by 60-80% (similar to YC success stories like Yuma)
- **Customer Experience**: Improve satisfaction scores through personalized, context-aware interactions
- **Scalability**: Handle unlimited concurrent conversations with consistent quality
- **Zero-risk deployment**: Autonomous agent runs parallel to current system for safe testing

## What
An autonomous order processing agent that:
- **Dynamically selects actions** instead of using fixed if/else logic
- **Evaluates goals** against multiple business objectives (satisfaction, value, efficiency, relationship)
- **Uses context-aware reasoning** considering customer history, preferences, and situation
- **Provides proactive suggestions** based on customer behavior patterns
- **Learns from outcomes** to improve future interactions
- **Integrates with existing Supabase infrastructure** and OpenAI API

### Success Criteria
- [ ] Agent processes orders with 85%+ accuracy compared to human baseline
- [ ] Average order value increases by 15% in test scenarios
- [ ] Customer satisfaction scores improve by 10% in autonomous conversations
- [ ] Processing time reduces by 60% for standard orders
- [ ] Agent operates safely in parallel to existing system with feature flags
- [ ] All validation tests pass (syntax, unit tests, integration tests)

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/agents/
  why: Core agent architecture, tools, dependencies, run patterns
  critical: Agent execution patterns and type-safe configuration
  
- url: https://ai.pydantic.dev/multi-agent-applications/
  why: Multi-agent coordination patterns for complex workflows
  critical: Agent delegation and programmatic hand-off patterns

- file: examples/example_pydantic_ai.py
  why: Dependency injection pattern using PydanticAIDeps dataclass
  critical: Supabase integration and async/await patterns

- file: ai-agent/agents/order_agent.py
  why: Current streamlined implementation to understand existing patterns
  critical: Message processing workflow and product matching logic

- file: ai-agent/schemas/order.py
  why: Existing order schemas and validation patterns
  critical: OrderCreation, OrderProduct, and database integration patterns

- file: ai-agent/tools/supabase_tools.py
  why: Database interaction patterns and existing tool functions
  critical: create_order, fetch_product_catalog, update_message_ai_data patterns

- doc: https://supabase.com/docs/reference/python/introduction
  section: Python client patterns for database operations
  critical: Async operations and error handling patterns

- doc: https://platform.openai.com/docs/api-reference
  section: Function calling and structured outputs
  critical: Tool definitions and response formatting
```

### Current Codebase Tree (relevant sections)
```bash
ai-agent/
├── agents/
│   ├── __init__.py
│   ├── order_agent.py                    # Current streamlined agent
│   └── session_aware_order_agent.py      # Session management
├── schemas/
│   ├── __init__.py
│   ├── message.py                        # Message analysis schemas
│   ├── order.py                          # Order creation schemas
│   └── product.py                        # Product schemas
├── services/
│   ├── __init__.py
│   ├── database.py                       # Supabase client setup
│   ├── order_session_manager.py          # Session state management
│   ├── pattern_detector.py               # Pattern detection
│   └── product_matcher.py                # Product matching logic
├── tools/
│   ├── __init__.py
│   └── supabase_tools.py                 # Database interaction tools
├── config/
│   ├── __init__.py
│   └── settings.py                       # Configuration management
└── main.py                               # Entry point
```

### Desired Codebase Tree with new autonomous agent files
```bash
ai-agent/
├── agents/
│   ├── autonomous_order_agent.py         # NEW: Main autonomous agent
│   ├── agent_factory.py                  # NEW: Factory to choose between agents
│   └── [existing files]
├── schemas/
│   ├── autonomous_agent.py               # NEW: Autonomous agent schemas
│   ├── goals.py                          # NEW: Business goals and evaluation
│   └── [existing files]
├── tools/
│   ├── autonomous_actions.py             # NEW: Autonomous agent actions
│   └── [existing files]
├── services/
│   ├── goal_evaluator.py                 # NEW: Goal evaluation service
│   ├── conversation_memory.py            # NEW: Enhanced memory system
│   └── [existing files]
├── config/
│   ├── feature_flags.py                  # NEW: Feature flag management
│   └── [existing files]
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Pydantic AI requires proper async/await patterns
# - All agent runs must use async functions
# - Tools must be properly decorated with @agent.tool
# - Dependencies injection uses deps_type parameter

# CRITICAL: Supabase client patterns
# - Always use async client methods (await client.table().insert())
# - Handle exceptions with try/catch for database operations
# - Use get_current_distributor_id() for multi-tenant isolation

# CRITICAL: OpenAI function calling patterns
# - Tools must have clear Pydantic input/output models
# - Use structured outputs for consistent responses
# - Handle rate limiting and token usage tracking

# CRITICAL: Feature flag implementation
# - Must support gradual rollout (percentage-based)
# - Fallback to existing agent when autonomous fails
# - Environment variable configuration for safety

# CRITICAL: Goal evaluation system
# - Must be deterministic and explainable
# - Confidence scores must be properly weighted
# - Business goal weights must be configurable per distributor
```

## Implementation Blueprint

### Data Models and Structure

Core business goals and action evaluation models for autonomous decision making:

```python
# schemas/goals.py
from pydantic import BaseModel, Field
from typing import Dict, List
from enum import Enum

class BusinessGoalType(str, Enum):
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    ORDER_VALUE = "order_value" 
    EFFICIENCY = "efficiency"
    RELATIONSHIP_BUILDING = "relationship_building"

class BusinessGoal(BaseModel):
    name: BusinessGoalType
    weight: float = Field(ge=0.0, le=1.0)
    description: str
    metrics: List[str]

class ActionEvaluation(BaseModel):
    action_name: str
    goal_scores: Dict[str, float]  # Goal name -> score (0.0-1.0)
    overall_score: float
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)

# schemas/autonomous_agent.py
class AutonomousAgentContext(BaseModel):
    customer_id: str
    conversation_history: List[Dict]
    customer_preferences: Dict
    inventory_status: Dict
    time_context: Dict
    business_goals: List[BusinessGoal]

class AutonomousAction(BaseModel):
    action_type: str
    parameters: Dict
    confidence: float
    reasoning: str
    expected_outcomes: List[str]
```

### List of Tasks to Complete (in order)

```yaml
Task 1 - Create Business Goals Schema:
CREATE ai-agent/schemas/goals.py:
  - DEFINE BusinessGoalType enum with core goal types
  - CREATE BusinessGoal model with weights and metrics
  - CREATE ActionEvaluation model for scoring actions
  - INCLUDE proper validation and documentation

Task 2 - Create Autonomous Agent Schema:
CREATE ai-agent/schemas/autonomous_agent.py:
  - DEFINE AutonomousAgentContext for rich context
  - CREATE AutonomousAction model for action representation
  - MIRROR validation patterns from existing schemas/order.py
  - INCLUDE memory and learning structures

Task 3 - Create Goal Evaluator Service:
CREATE ai-agent/services/goal_evaluator.py:
  - IMPLEMENT goal scoring algorithms
  - CREATE weighted evaluation functions
  - INCLUDE explainable decision logic
  - MIRROR async patterns from existing services

Task 4 - Create Enhanced Memory Service:
CREATE ai-agent/services/conversation_memory.py:
  - IMPLEMENT customer preference learning
  - CREATE conversation context management
  - INCLUDE successful pattern storage
  - INTEGRATE with existing database patterns

Task 5 - Create Autonomous Actions Tools:
CREATE ai-agent/tools/autonomous_actions.py:
  - IMPLEMENT all autonomous actions (create_order, ask_clarification, etc.)
  - MIRROR tool patterns from existing tools/supabase_tools.py
  - INCLUDE proper Pydantic AI tool decorators
  - CREATE goal-aware action implementations

Task 6 - Create Feature Flag Configuration:
CREATE ai-agent/config/feature_flags.py:
  - IMPLEMENT percentage-based rollout system
  - CREATE safe fallback mechanisms
  - INCLUDE environment variable management
  - MIRROR settings patterns from config/settings.py

Task 7 - Create Main Autonomous Agent:
CREATE ai-agent/agents/autonomous_order_agent.py:
  - IMPLEMENT main AutonomousOrderAgent class
  - MIRROR dependency injection from examples/example_pydantic_ai.py
  - INCLUDE goal-oriented decision making loop
  - CREATE comprehensive error handling and fallbacks

Task 8 - Create Agent Factory:
CREATE ai-agent/agents/agent_factory.py:
  - IMPLEMENT agent selection logic based on feature flags
  - CREATE seamless fallback to existing order_agent
  - INCLUDE A/B testing capabilities
  - MIRROR factory patterns from existing codebase

Task 9 - Update Main Entry Point:
MODIFY ai-agent/main.py:
  - INTEGRATE agent factory for agent selection
  - PRESERVE existing functionality as fallback
  - INCLUDE feature flag checking
  - MAINTAIN existing webhook integration

Task 10 - Create Comprehensive Tests:
CREATE ai-agent/tests/test_autonomous_order_agent.py:
  - IMPLEMENT unit tests for all new components
  - CREATE integration tests with mock scenarios
  - INCLUDE goal evaluation testing
  - MIRROR test patterns from existing tests/
```

### Per Task Pseudocode

```python
# Task 3: Goal Evaluator Service
class GoalEvaluator:
    async def evaluate_action(
        self, 
        action: AutonomousAction,
        context: AutonomousAgentContext,
        goals: List[BusinessGoal]
    ) -> ActionEvaluation:
        # PATTERN: Score each action against all business goals
        goal_scores = {}
        
        for goal in goals:
            # CRITICAL: Use deterministic scoring algorithms
            score = await self._score_action_for_goal(action, goal, context)
            goal_scores[goal.name] = score
        
        # PATTERN: Calculate weighted overall score
        overall_score = sum(
            goal_scores[goal.name] * goal.weight 
            for goal in goals
        )
        
        return ActionEvaluation(
            action_name=action.action_type,
            goal_scores=goal_scores,
            overall_score=overall_score,
            reasoning=self._generate_reasoning(action, goal_scores),
            confidence=self._calculate_confidence(goal_scores)
        )

# Task 7: Main Autonomous Agent
class AutonomousOrderAgent:
    def __init__(self, database: DatabaseService, distributor_id: str):
        # PATTERN: Use PydanticAIDeps for dependency injection
        self.deps = AutonomousAgentDeps(
            database=database,
            distributor_id=distributor_id,
            goal_evaluator=GoalEvaluator(),
            memory_service=ConversationMemory()
        )
        
        # CRITICAL: Configure agent with tools and model
        self.agent = Agent(
            model=OpenAIModel(settings.openai_model),
            deps_type=AutonomousAgentDeps,
            tools=[
                self.create_order_tool,
                self.ask_clarification_tool,
                # ... other autonomous actions
            ],
            retries=2
        )
    
    async def process_message(self, message_data: Dict) -> Optional[AutonomousResult]:
        # PATTERN: Build rich context for decision making
        context = await self._build_autonomous_context(message_data)
        
        # PATTERN: Get available actions from AI
        available_actions = await self._get_available_actions(context)
        
        # PATTERN: Evaluate each action against business goals
        evaluations = []
        for action in available_actions:
            evaluation = await self.deps.goal_evaluator.evaluate_action(
                action, context, self.deps.business_goals
            )
            evaluations.append(evaluation)
        
        # PATTERN: Select best action based on weighted scores
        best_action = max(evaluations, key=lambda e: e.overall_score)
        
        # CRITICAL: Execute action if confidence > threshold
        if best_action.confidence >= settings.autonomous_confidence_threshold:
            return await self._execute_action(best_action, context)
        else:
            # FALLBACK: Use existing streamlined agent
            return await self._fallback_to_existing_agent(message_data)
```

### Integration Points
```yaml
DATABASE:
  - table: ai_responses - track autonomous decisions for learning
  - table: ai_usage_metrics - monitor autonomous agent usage
  - column: messages.autonomous_processed - flag autonomous processing
  
CONFIG:
  - add to: config/settings.py
  - pattern: "AUTONOMOUS_AGENT_ENABLED = bool(os.getenv('AUTONOMOUS_AGENT_ENABLED', 'false'))"
  - pattern: "AUTONOMOUS_CONFIDENCE_THRESHOLD = float(os.getenv('AUTONOMOUS_CONFIDENCE_THRESHOLD', '0.8'))"
  
ROUTES:
  - modify: ai-agent/api.py
  - pattern: Use agent_factory to select agent type
  - preserve: All existing webhook endpoints and logic

FEATURE_FLAGS:
  - environment: USE_AUTONOMOUS_AGENT=false (master switch)
  - environment: AUTONOMOUS_AGENT_PERCENTAGE=0 (gradual rollout)
  - environment: AUTONOMOUS_AGENT_GOALS_ENABLED=true (goal evaluation)
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd ai-agent
ruff check --fix .                    # Auto-fix formatting
mypy .                                # Type checking
python -m pytest tests/ --collect-only # Verify test discovery

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE tests/test_autonomous_order_agent.py with these test cases:
def test_goal_evaluation_scoring():
    """Goal evaluator produces consistent scores"""
    evaluator = GoalEvaluator()
    action = AutonomousAction(action_type="create_order", ...)
    context = AutonomousAgentContext(...)
    goals = [BusinessGoal(name="customer_satisfaction", weight=0.4)]
    
    result = await evaluator.evaluate_action(action, context, goals)
    assert 0.0 <= result.overall_score <= 1.0
    assert result.reasoning is not None

def test_autonomous_agent_fallback():
    """Agent falls back to existing system when confidence low"""
    agent = AutonomousOrderAgent(mock_database, "test_distributor")
    
    with mock.patch.object(agent, '_get_best_action_evaluation') as mock_eval:
        mock_eval.return_value.confidence = 0.5  # Below threshold
        
        result = await agent.process_message({"content": "test message"})
        # Should use fallback, not autonomous processing

def test_feature_flag_integration():
    """Feature flags control agent selection"""
    with mock.patch.dict(os.environ, {'USE_AUTONOMOUS_AGENT': 'false'}):
        factory = AgentFactory(mock_database, "test_distributor")
        agent = await factory.create_agent()
        assert isinstance(agent, StreamlinedOrderProcessor)
```

```bash
# Run and iterate until passing:
python -m pytest tests/test_autonomous_order_agent.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test autonomous agent in realistic scenario
cd ai-agent
python -c "
import asyncio
from main import main
from config.settings import settings
import os

# Enable autonomous agent for testing
os.environ['USE_AUTONOMOUS_AGENT'] = 'true'
os.environ['AUTONOMOUS_AGENT_PERCENTAGE'] = '100'

# Test message processing
test_message = {
    'id': 'test123',
    'content': 'Quiero dos botellas de leche',
    'customer_id': 'customer123',
    'conversation_id': 'conv123'
}

async def test():
    from agents.agent_factory import AgentFactory
    from services.database import DatabaseService
    
    db = DatabaseService()
    factory = AgentFactory(db, 'distributor123')
    agent = await factory.create_agent()
    
    result = await agent.process_message(test_message)
    print(f'Result: {result}')
    print(f'Agent type: {type(agent).__name__}')

asyncio.run(test())
"

# Expected: Autonomous agent processes message with goal evaluation
# Check logs for decision reasoning and goal scores
```

## Final Validation Checklist
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `ruff check ai-agent/`
- [ ] No type errors: `mypy ai-agent/`
- [ ] Feature flags work: Test with different environment variables
- [ ] Agent selection works: Factory chooses correct agent based on flags
- [ ] Goal evaluation produces explainable decisions
- [ ] Fallback mechanism activates when confidence low
- [ ] Database integration maintains existing patterns
- [ ] Autonomous actions execute successfully
- [ ] Memory system tracks customer preferences
- [ ] Error cases handled gracefully with fallback

---

## Anti-Patterns to Avoid
- ❌ Don't bypass existing database patterns - use established tools
- ❌ Don't skip goal evaluation validation - decisions must be explainable  
- ❌ Don't ignore confidence thresholds - safety first
- ❌ Don't break existing agent functionality - parallel implementation
- ❌ Don't hardcode business goal weights - make them configurable
- ❌ Don't forget async/await patterns - everything must be async
- ❌ Don't skip comprehensive error handling - autonomous agents need graceful degradation

---

## Confidence Score: 9/10

This PRP provides comprehensive context for one-pass implementation success:

**Strengths:**
- Complete codebase analysis with existing patterns identified
- Detailed implementation blueprint with specific file paths
- Comprehensive external research on Pydantic AI autonomous agents
- Clear goal-oriented decision making architecture
- Safe parallel implementation with feature flags
- Executable validation loops at multiple levels
- Anti-patterns explicitly documented

**Areas requiring attention during implementation:**
- Goal evaluation algorithms need careful tuning for business objectives
- Memory system integration with existing conversation patterns
- Performance optimization for real-time decision making

The PRP follows established codebase patterns while introducing autonomous capabilities through a safe, feature-flagged approach that enables gradual rollout and easy rollback.