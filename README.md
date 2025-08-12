# Macro-Economic SQL Agent

This project implements a "Text-to-SQL" agent that can answer natural language questions about macro-economic data. It leverages the `google-adk` framework to create a robust pipeline for query generation, validation, execution, and answer synthesis.

## Features

-   **Natural Language to SQL**: Translates human-language questions into valid SQLite queries.
-   **Query Validation**: Safely validates generated SQL queries for syntactic correctness and schema adherence before execution.
-   **Modular Architecture**: Built as a `SequentialAgent` composed of specialized sub-agents, making it easy to extend and maintain.
-   **Async Operations**: Utilizes `aiosqlite` for non-blocking database interactions.
-   **Pre-packaged Data**: Comes with a dataset of world bank economic indicators for various countries.

## Architecture

The core of the project is a `SequentialAgent` that processes a user's request through a series of sub-agents:

1.  **Query Generation Agent**: Takes a natural language question (e.g., "What was the GDP of France in 2023?") and generates a corresponding SQL query.
2.  **Query Validation Agent**: Inspects the generated SQL to ensure it is syntactically correct and references valid tables and columns. This prevents errors and potential security issues.
3.  **Query Runner Agent**: Executes the validated SQL query against the SQLite database.
4.  **Answer Generation Agent**: Receives the results from the query runner and synthesizes a human-readable answer.

## Data Schema

The agent operates on a single table (derived from `world_bank_data_2025.csv`) with the following schema:

| Column Name              | Description                                      |
| ------------------------ | ------------------------------------------------ |
| `country_name`           | Extended country name the data refers to.        |
| `country_id`             | 2-letter ID of the country.                      |
| `year`                   | Year the data refers to.                         |
| `inflation`              | Inflation figures (CPI %).                       |
| `gdp`                    | GDP figure.                                      |
| `gdp_per_capita`         | GDP per capita numbers.                          |
| `unemployment_rate`      | Unemployment rate.                               |
| `interest_rate`          | Real interest rate.                              |
| `inflation_gdp_deflator` | Inflation as GDP deflator.                       |
| `gdp_growth`             | GDP growth as an annual percentage.              |
| `current_account_balance`| Current Account Balance as % of GDP.             |
| `government_expense`     | Government expense as % of GDP.                  |
| `government_revenue`     | Government revenue as % of GDP.                  |
| `tax_revenue`            | Tax revenue as % of GDP.                         |
| `gross_national_income`  | Gross national income in USD.                    |
| `public_debt`            | Public debt as a percentage of GDP.              |

## Installation

This project uses `uv` for dependency management.

1.  **Install `uv`**:
    If you don't have `uv` installed, follow the official installation instructions:
    ```bash
    pip install uv
    ```

2.  **Create a Virtual Environment**:
    ```bash
    uv venv
    ```

3.  **Activate the Virtual Environment**:
    -   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    -   On Windows:
        ```bash
        .venv\\Scripts\\activate
        ```

4.  **Install Dependencies**:
    ```bash
    uv pip install -r requirements.txt
    ```

## Usage

To use the agent, you can import the `root_agent` and call its `invoke` method with a natural language question.

Here is an example script:

```python
import asyncio
from agent_sql_economic.agent import root_agent

async def main():
    """Asynchronously runs the agent and prints the response."""
    question = "What was the gdp and inflation for the US in 2025?"
    try:
        response = await root_agent.invoke({"question": question})
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())

```
Save this script (e.g., `run_agent.py`) and execute it:
```bash
python run_agent.py
```

## Testing

The project uses `pytest` for testing. To run the test suite, execute the following command in the root directory:

```bash
pytest
```
