# 🎯 Goal Configuration Examples

## Quick Start: Using Preset Profiles

### 1. Balanced Mode (Default)
```bash
GOAL_TYPE=balanced
```
Agent behavior:
- Balances all goals equally
- Good for general B2B operations
- Creates orders when confident
- Asks questions when unsure

### 2. Revenue-Focused Mode
```bash
GOAL_TYPE=revenue
```
Agent behavior:
- Prioritizes maximizing order value (45%)
- More aggressive with suggestions
- Tries to upsell and cross-sell
- Still maintains customer satisfaction

### 3. Service-Focused Mode
```bash
GOAL_TYPE=service
```
Agent behavior:
- Prioritizes customer happiness (50%)
- More careful and thorough
- Asks more clarifying questions
- Less aggressive with sales

## Custom Goal Configuration

### Example 1: Aggressive Sales Agent
```bash
GOAL_TYPE=custom
USE_CUSTOM_GOALS=true
GOAL_CUSTOMER_SATISFACTION=0.20    # 20% - Still care about customers
GOAL_ORDER_VALUE=0.60               # 60% - Heavy focus on revenue
GOAL_EFFICIENCY=0.15                # 15% - Quick processing
GOAL_RELATIONSHIP_BUILDING=0.05     # 5% - Minimal relationship focus

# Lower thresholds for more aggressive behavior
AUTONOMOUS_ORDER_CONFIDENCE=0.75    # Create orders with less certainty
GOAL_CONFIDENCE_THRESHOLD=0.70      # Lower overall confidence needed
```

### Example 2: Conservative Customer Service
```bash
GOAL_TYPE=custom
USE_CUSTOM_GOALS=true
GOAL_CUSTOMER_SATISFACTION=0.60    # 60% - Customer first
GOAL_ORDER_VALUE=0.15              # 15% - Revenue secondary
GOAL_EFFICIENCY=0.10               # 10% - Take time if needed
GOAL_RELATIONSHIP_BUILDING=0.15    # 15% - Build trust

# Higher thresholds for safety
AUTONOMOUS_ORDER_CONFIDENCE=0.90    # Very sure before creating orders
GOAL_CONFIDENCE_THRESHOLD=0.85      # High confidence required
```

### Example 3: Efficiency-Focused Operation
```bash
GOAL_TYPE=custom
USE_CUSTOM_GOALS=true
GOAL_CUSTOMER_SATISFACTION=0.30    # 30% - Good service
GOAL_ORDER_VALUE=0.25              # 25% - Decent revenue
GOAL_EFFICIENCY=0.40               # 40% - Fast processing priority
GOAL_RELATIONSHIP_BUILDING=0.05    # 5% - Basic relationships

# Balanced thresholds
AUTONOMOUS_ORDER_CONFIDENCE=0.80    # Standard confidence
GOAL_CONFIDENCE_THRESHOLD=0.75      # Slightly lower for speed
```

## Understanding the Impact

### High Customer Satisfaction Weight
- Agent asks more clarifying questions
- Double-checks order details
- Provides detailed responses
- May sacrifice speed for accuracy

### High Order Value Weight  
- Agent suggests complementary products
- Mentions bulk discounts
- Tries to increase order size
- May be more pushy

### High Efficiency Weight
- Agent processes quickly
- Makes faster decisions
- Less back-and-forth
- May miss upsell opportunities

### High Relationship Building Weight
- Agent remembers preferences
- Personalizes interactions
- Builds rapport over time
- May sacrifice immediate sales

## Testing Different Configurations

1. **Week 1**: Start with `GOAL_TYPE=balanced`
2. **Week 2**: Try `GOAL_TYPE=revenue` and compare results
3. **Week 3**: Test custom weights based on your findings
4. **Ongoing**: Adjust based on customer feedback and metrics

## Important Notes

- Weights don't need to sum to 1.0 (they're auto-normalized)
- Changes take effect on API restart
- Monitor logs to see which goals influence decisions
- Customer preferences are learned regardless of weights