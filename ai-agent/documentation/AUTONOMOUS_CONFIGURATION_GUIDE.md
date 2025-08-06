# 🎛️ Autonomous Agent Configuration Guide

## 1. Business Goal Weights (Most Important!)

The autonomous agent makes decisions based on 4 business goals. You can adjust their weights:

### Default Goal Configurations

Located in `ai-agent/schemas/goals.py`:

#### **Balanced Mode** (Default)
```python
CUSTOMER_SATISFACTION: 0.35  # 35% - Customer happiness
ORDER_VALUE: 0.30            # 30% - Revenue maximization  
EFFICIENCY: 0.25             # 25% - Quick processing
RELATIONSHIP_BUILDING: 0.10   # 10% - Long-term loyalty
```

#### **Revenue-Focused Mode**
```python
ORDER_VALUE: 0.45            # 45% - Aggressive revenue focus
CUSTOMER_SATISFACTION: 0.25  # 25% - Maintain satisfaction
EFFICIENCY: 0.20             # 20% - Process efficiently
RELATIONSHIP_BUILDING: 0.10   # 10% - Build relationships
```

#### **Service-Focused Mode**
```python
CUSTOMER_SATISFACTION: 0.50  # 50% - Exceptional service
RELATIONSHIP_BUILDING: 0.25   # 25% - Strong relationships
EFFICIENCY: 0.15             # 15% - Efficient service
ORDER_VALUE: 0.10            # 10% - Natural upsells
```

## 2. Confidence Thresholds

Control how confident the agent must be before taking actions:

### In `ai-agent/config/feature_flags.py`:
```python
# Minimum confidence required for each action type
AUTONOMOUS_ORDER_CREATION: 0.85      # 85% - Very high confidence needed
PRODUCT_SUGGESTIONS: 0.70            # 70% - Medium confidence
CLARIFICATION_REQUESTS: 0.60         # 60% - Lower confidence OK
```

### In `ai-agent/schemas/goals.py`:
```python
confidence_threshold: 0.8  # Overall confidence threshold
score_threshold: 0.7      # Minimum action score threshold
```

## 3. Feature Flags (On/Off Switches)

### Environment Variables in `.env`:
```bash
# Master switches
USE_AUTONOMOUS_AGENT=true           # Enable/disable autonomous agent
AUTONOMOUS_FALLBACK_ENABLED=true    # Enable fallback to streamlined agent

# Individual features
AUTONOMOUS_GOAL_EVALUATION_ENABLED=true    # Goal-based decisions
AUTONOMOUS_MEMORY_LEARNING_ENABLED=true    # Learn preferences
AUTONOMOUS_ORDER_CREATION=true             # Create orders autonomously
AUTONOMOUS_PRODUCT_SUGGESTIONS=true        # Suggest products
AUTONOMOUS_CLARIFICATION_REQUESTS=true     # Ask clarifying questions
AUTONOMOUS_PREFERENCE_LEARNING=true        # Remember customer preferences
```

## 4. Rollout Percentages

For gradual deployment (in `ai-agent/config/feature_flags.py`):

```bash
# Environment variables for percentage-based rollout
AUTONOMOUS_AUTONOMOUS_AGENT_ENABLED_PERCENTAGE=50  # 50% of customers
AUTONOMOUS_ORDER_CREATION_PERCENTAGE=25            # 25% get auto-orders
```

## 5. Action Evaluation Weights

In `ai-agent/services/goal_evaluator.py`, the agent scores actions based on:

- **Customer Satisfaction**: Response time, accuracy, fulfillment
- **Order Value**: Number of products, total value, upsell potential
- **Efficiency**: Processing speed, automation rate
- **Relationship Building**: Personalization, preference learning

## 📝 How to Customize

### Option 1: Change Goal Weights (Recommended)
Edit `ai-agent/agents/autonomous_order_agent.py` constructor:
```python
# Change from "balanced" to "revenue" or "service"
self.business_goals = create_default_goal_configuration(
    distributor_id, 
    "revenue"  # or "service" or "balanced"
).goals
```

### Option 2: Create Custom Goal Configuration
```python
custom_goals = [
    BusinessGoal(
        name=BusinessGoalType.CUSTOMER_SATISFACTION,
        weight=0.40,  # Your custom weight
        description="Focus on customer happiness"
    ),
    # ... other goals
]
```

### Option 3: Adjust Confidence Thresholds
In `.env`:
```bash
# Add these to customize thresholds
AUTONOMOUS_CONFIDENCE_THRESHOLD=0.75  # Lower = more aggressive
AUTONOMOUS_SCORE_THRESHOLD=0.65       # Lower = more actions taken
```

### Option 4: Enable/Disable Features
Toggle individual features in `.env` as needed.

## 🎯 Recommended Configurations

### For Testing/Development
- Use current settings (all features enabled)
- Lower confidence thresholds for more activity

### For Conservative Deployment
```bash
USE_AUTONOMOUS_AGENT=true
AUTONOMOUS_ORDER_CREATION=false  # Disable auto-orders initially
# Keep suggestions and clarifications enabled
```

### For Revenue Optimization
- Switch to "revenue" goal configuration
- Keep high confidence thresholds
- Enable all features

### For Customer Service Focus
- Switch to "service" goal configuration  
- Lower confidence thresholds
- Focus on clarifications and suggestions

## 📊 Monitoring Impact

Watch these metrics to tune your configuration:
- Order creation rate
- Customer satisfaction (response quality)
- Processing time
- Revenue per conversation
- Fallback frequency

## 🔧 Quick Tuning Tips

1. **Too Conservative?** Lower confidence thresholds
2. **Too Aggressive?** Raise confidence thresholds or adjust goal weights
3. **Not Enough Orders?** Increase ORDER_VALUE weight
4. **Customer Complaints?** Increase CUSTOMER_SATISFACTION weight
5. **Too Slow?** Increase EFFICIENCY weight