# Personal Finance AI Agent  
**Hybrid Rule-Based + LLM Transaction Categorization System**

## Overview

This project is a **production-style personal finance transaction categorization agent** that combines:

- Deterministic, rule-based categorization  
- Confidence scoring  
- Intelligent escalation to a Large Language Model (LLM) when rules are uncertain  

The system is designed to be:
- Cost-aware  
- Explainable  
- Extensible  
- Suitable for real-world financial data pipelines  

This is **not** a pure “LLM app.” The LLM is used **only when needed**.

---

## Architecture Summary

### High-Level Flow

1. Load raw transaction data from CSV  
2. Apply rule-based categorization  
3. Assign a confidence score  
4. Route transactions:
   - High confidence → accept rule result  
   - Low confidence → escalate to LLM  
5. Persist enriched results to CSV  

---

## Project Structure

```
Personal_Finance_Agent/
├── src/
│   ├── agents/
│   │   ├── ingestion_agent.py          # Loads CSV data into dictionaries
│   │   ├── categorization_agent.py     # Rule-based categorization
│   │   ├── llm_categorization_agent.py # LLM-powered categorization
│   │   └── routing.py                  # Confidence-based routing logic
│   ├── config/
│   │   ├── categories.py               # Allowed category definitions
│   │   └── settings.py                 # Environment configuration (API keys)
│   └── main.py                         # Entry point orchestrates the pipeline
├── data/
│   ├── raw/
│   │   └── transactions.csv            # Input transaction data
│   └── processed/
│       └── categorized_transactions.csv # Output with categories
└── requirements.txt
```

---

## Component Responsibilities

### IngestionAgent
- Reads raw CSV files  
- Normalizes input into dictionaries  
- Does **not** categorize or score  

### CategorizationAgent (Rule-Based)
- Applies keyword rules  
- Returns:
  - `category`
  - `confidence`
  - `reason`
- **Does NOT decide final output**
- **Does NOT write to CSV**

### Routing (`src/agents/routing.py`)
- Central decision-maker  
- Accepts rule results  
- Escalates to LLM when confidence is below threshold  
- Annotates `source` (`rule` or `llm`)  
- Controls overall system behavior  

### LLMCategorizationAgent
- Uses OpenAI GPT-5-mini  
- Handles ambiguous transactions  
- Returns structured JSON only  
- Includes defensive parsing and fallback behavior  

---

## Confidence-Based Routing Logic

### Threshold-Based Decision Making

The routing logic in `src/agents/routing.py` uses a **confidence threshold** to determine when to escalate:

```python
CONFIDENCE_THRESHOLD = 0.6  # Configurable threshold

if rule_result["confidence"] >= CONFIDENCE_THRESHOLD:
    # Accept rule-based categorization
    return {**rule_result, "source": "rule"}
else:
    # Escalate to LLM for ambiguous cases
    llm_result = llm_agent.categorize(transaction)
    return {**llm_result, "source": "llm"}
```

### Decision Flow

1. **Rule-Based Categorization** (`CategorizationAgent`)
   - Matches transaction description against keyword rules
   - Returns `confidence` score (typically 0.9 for matches, 0.3 for no match)

2. **Routing Decision** (`route_transaction`)
   - If `confidence >= 0.6` → **Use rule result** (no LLM cost)
   - If `confidence < 0.6` → **Escalate to LLM** (cost incurred)

3. **LLM Categorization** (`LLMCategorizationAgent`)
   - Only called when rules are uncertain
   - Returns structured JSON: `category`, `confidence`, `reason`
   - Includes fallback handling for malformed responses

### Output Annotation

Each transaction in the final output includes:
- `category`: Final category assignment
- `confidence`: Confidence score (0-1)
- `reason`: Explanation of categorization decision
- `source`: `"rule"` or `"llm"` (indicates which agent made the decision)
- `rule_confidence`: Original rule confidence (if escalated to LLM)

---

## Data Flow

```
CSV Input
    ↓
IngestionAgent.load_transactions()
    ↓
[List of transaction dicts]
    ↓
For each transaction:
    ↓
CategorizationAgent.categorize()
    ↓
[category, confidence, reason]
    ↓
route_transaction() → Decision Point
    ├─ confidence >= 0.6 → Use rule result
    └─ confidence < 0.6 → LLMCategorizationAgent.categorize()
    ↓
Final result with source annotation
    ↓
Write to CSV Output
```

---

## Key Design Principles

1. **Cost Optimization**: LLM only used when rule-based approach is uncertain (confidence < threshold)

2. **Explainability**: Every categorization includes a `reason` field explaining the decision

3. **Defensive Programming**: 
   - JSON parsing fallbacks in LLM agent
   - Error handling in main pipeline
   - Type assertions where appropriate

4. **Separation of Concerns**:
   - Agents don't write to files
   - Routing logic is centralized
   - Each component has a single responsibility

---

## Configuration

### Adjusting Confidence Threshold

Edit `CONFIDENCE_THRESHOLD` in `src/agents/routing.py`:
- **Higher threshold** (e.g., 0.8) → More LLM calls, higher accuracy
- **Lower threshold** (e.g., 0.4) → Fewer LLM calls, lower cost

### Adding Category Rules

Edit `CATEGORY_RULES` in `src/agents/categorization_agent.py`:
```python
CATEGORY_RULES = {
    "CategoryName": ["keyword1", "keyword2", ...],
    ...
}
```

### Allowed Categories

Edit `ALLOWED_CATEGORIES` in `src/config/categories.py` to restrict LLM output.

---

## Usage Example

```python
from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import CategorizationAgent
from agents.llm_categorization_agent import LLMCategorizationAgent
from agents.routing import route_transaction

# Load transactions
ingestion = IngestionAgent("data/raw/transactions.csv")
transactions = ingestion.load_transactions()

# Initialize agents
rule_agent = CategorizationAgent()
llm_agent = LLMCategorizationAgent()

# Process each transaction
for txn in transactions:
    rule_result = rule_agent.categorize(txn)
    final = route_transaction(rule_result, txn, llm_agent)
    # final contains: category, confidence, reason, source
```

---

## Expected Output Format

Each row in `categorized_transactions.csv` includes original transaction fields plus:
- `category`: Assigned category
- `confidence`: Confidence score (0-1)
- `reason`: Explanation
- `source`: `"rule"` or `"llm"`
- `rule_confidence`: Original rule confidence (if escalated)