## Demo commands for Personal Finance Agent

All commands assume you run them from the project root:

```bash
cd Personal_Finance_Agent
```

### 1. Basic processing (categorization + analytics + anomalies)

```bash
python src/main.py
```

**Offline (no LLM, forced):**

```bash
python src/main.py --no-llm
```

### 2. Generate offline dashboard and forecasts

```bash
python src/main.py --no-llm --dashboard --months-ahead 3
```

Outputs to highlight (in `data/processed/`):
- `dashboard.html`
- `spending_forecast.csv`
- `spending_summary.txt`
- `monthly_summary.csv`
- `anomaly_report.txt`
- `bill_calendar.csv`
- `budget_status.json`
- `financial_health.json`

### 3. Conversational questions (CLI chat, offline)

You can append `--ask "..."` to any run. Examples:

```bash
python src/main.py --no-llm --ask "compare this month vs last month"
python src/main.py --no-llm --ask "how much did I spend on dining last month?"
python src/main.py --no-llm --ask "show transactions over $100"
```

### 4. LLM-enabled mode (if you have an OpenAI key)

In PowerShell (current session only):

```powershell
$env:OPENAI_API_KEY = "YOUR_API_KEY_HERE"
python src/main.py --ask "compare this month vs last month"
```

To explicitly disable LLM even with a key set:

```bash
python src/main.py --no-llm
```

### 5. Quick test suite run (for live coding/demo)

```bash
python -m unittest discover -s tests -p "test_*.py"
```

