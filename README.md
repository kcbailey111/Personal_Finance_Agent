# Personal Finance Agent

An autonomous AI agent system that analyzes personal financial data to identify anomalies, forecast spending, and provide actionable financial recommendations. The system uses a multi-agent architecture with structured communication, domain heuristics, and LLM-assisted reasoning to deliver explainable financial insights.

## Features

- **Transaction Ingestion**: Loads and processes financial transactions from CSV files
- **Intelligent Categorization**: Multi-agent categorization system using rule-based and LLM-powered approaches
- **Anomaly Detection**: Identifies unusual spending patterns and outliers
- **Spending Forecasting**: Predicts future spending trends based on historical data
- **Actionable Recommendations**: Provides personalized financial advice based on analysis

## Architecture

The system follows a **multi-agent architecture** with specialized agents:

- **IngestionAgent**: Handles data loading and preprocessing
- **CategorizationAgent**: Rule-based transaction categorization using heuristics
- **LLMCategorizationAgent**: LLM-powered categorization for edge cases
- **Routing Logic**: Intelligently routes transactions between rule-based and LLM agents
- **ForecastingAgent**: Time-series forecasting for spending predictions
- **AnomalyDetectionAgent**: Statistical anomaly detection
- **RecommendationAgent**: Generates actionable financial recommendations

## Project Structure

```
Personal_Finance_Agent/
├── src/
│   ├── agents/           # Multi-agent system components
│   ├── config/           # Configuration files (prompts, categories, settings)
│   ├── tools/            # Utility tools (CSV loader, stats, forecasting)
│   ├── memory/           # Historical data and user profile management
│   ├── utils/            # Helper functions and validators
│   ├── evaluation/       # Testing and evaluation components
│   └── main.py           # Entry point
├── data/
│   ├── raw/              # Input transaction data
│   ├── processed/        # Processed/categorized outputs
│   └── rules/            # Budget rules and configuration
├── tests/                # Unit and integration tests
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   - Create a `.env` file in the project root
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

3. **Prepare data**:
   - Place your transaction CSV file in `data/raw/transactions.csv`
   - Ensure the CSV has required columns (date, amount, description, etc.)

## Usage

Run the main application:

```bash
python src/main.py
```

This will:
1. Load transactions from `data/raw/transactions.csv`
2. Process and categorize each transaction
3. Save categorized results to `data/processed/categorized_transactions.csv`

## Development Guidelines

- **Agent Design**: Each agent should have a single, well-defined responsibility
- **Error Handling**: Use try-except blocks and provide meaningful error messages
- **Logging**: Use the centralized logger in `src/logging/logger.py`
- **Testing**: Add tests in `tests/` for new features
- **Documentation**: Update relevant docs when adding new features

## Key Components

- **Agent Prompts**: Defined in `src/config/agent_prompts.yaml`
- **Categories**: Transaction categories in `src/config/categories.yaml`
- **Budget Rules**: Customizable rules in `data/rules/budget_rules.yaml`
- **Schema Validation**: Transaction schemas in `src/utils/schema.py`

## Next Steps

- [ ] Enhance anomaly detection algorithms
- [ ] Improve forecasting accuracy
- [ ] Add more recommendation strategies
- [ ] Implement user feedback loop
- [ ] Add visualization dashboard
