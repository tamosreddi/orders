# 🎯 Understanding Confidence Thresholds

## What Are Confidence Thresholds?

When the autonomous agent evaluates an action (like creating an order), it generates a **confidence score** from 0.0 to 1.0:
- 0.0 = No confidence at all
- 0.5 = 50% confident
- 0.85 = 85% confident (very sure)
- 1.0 = 100% confident

The agent will ONLY take an action if its confidence is ABOVE the threshold.

## Example Scenario

Customer says: "quiero dos botellas de leche"

The agent evaluates:
1. **Create Order Action**
   - Confidence: 0.90 (very clear request)
   - Threshold: 0.85
   - Result: ✅ WILL create order (0.90 > 0.85)

2. **Suggest Products Action**  
   - Confidence: 0.75 (could suggest related items)
   - Threshold: 0.70
   - Result: ✅ WILL suggest products (0.75 > 0.70)

Customer says: "necesito algo para la fiesta"

The agent evaluates:
1. **Create Order Action**
   - Confidence: 0.60 (unclear what they want)
   - Threshold: 0.85
   - Result: ❌ WON'T create order (0.60 < 0.85)

2. **Ask Clarification Action**
   - Confidence: 0.80 (definitely needs clarification)
   - Threshold: 0.60
   - Result: ✅ WILL ask for clarification (0.80 > 0.60)

## Where to Change These Thresholds

### Option 1: Edit the Source Code (Permanent Change)

File: `/Users/macbook/orderagent/ai-agent/config/feature_flags.py`

Line 305:
```python
minimum_confidence_threshold=0.85  # Change to 0.75 for less strict
```

Line 315:
```python
minimum_confidence_threshold=0.7   # Change to 0.6 for more suggestions
```

Line 325:
```python
minimum_confidence_threshold=0.6   # Change to 0.5 for more questions
```

### Option 2: Environment Variables (Not Yet Implemented)

Currently, these thresholds are hardcoded. If you want to make them configurable via .env, I can add that feature.

## Impact of Changing Thresholds

### Lower Thresholds (e.g., 0.85 → 0.70)
- ✅ More orders created automatically
- ✅ More proactive behavior
- ❌ Higher risk of mistakes
- ❌ May create wrong orders

### Higher Thresholds (e.g., 0.85 → 0.95)
- ✅ Very accurate when it acts
- ✅ Fewer mistakes
- ❌ Creates fewer orders
- ❌ More conservative/passive

## Recommended Settings by Business Type

### Conservative B2B (Current Default)
- Order Creation: 0.85
- Product Suggestions: 0.70
- Clarifications: 0.60

### Aggressive Sales
- Order Creation: 0.75
- Product Suggestions: 0.60
- Clarifications: 0.50

### Ultra-Safe Mode
- Order Creation: 0.95
- Product Suggestions: 0.80
- Clarifications: 0.70

## How the Agent Calculates Confidence

The confidence comes from:
1. **Message clarity** - "quiero 2 leche" = high confidence
2. **Product match** - Exact product found = higher confidence
3. **Customer history** - Repeat orders = higher confidence
4. **Context** - Previous messages in conversation
5. **Goal alignment** - How well action meets business goals