# Macro-Economic SQL Agent

This project implements a "Text-to-SQL" agent that can answer natural language questions about
macro-economic data.
It leverages the `google-adk` framework to create a robust pipeline for query
generation, validation, execution, and answer synthesis.

## Features

- **Natural Language to SQL**: Translates human-language questions into valid SQLite queries.
- **Query Validation**: Safely validates generated SQL queries for syntactic correctness and schema adherence before execution.
- **Modular Architecture**: Built as a `SequentialAgent` composed of specialized sub-agents, making it easy to extend and maintain.
- **Async Operations**: Utilizes `aiosqlite` for non-blocking database interactions.
- **Pre-packaged Data**: Comes with a dataset of world bank economic indicators for various countries.

## Architecture

The core of the project is a `SequentialAgent` that processes a user's request through a series of sub-agents:

1.  **Query Generation Agent**: Takes a natural language question (e.g., "What was the GDP of France in 2023?") and generates a corresponding SQL query.
2.  **Query Validation Agent**: Inspects the generated SQL to ensure it is syntactically correct and references valid tables and columns. This prevents errors and potential security issues.
3.  **Query Runner Agent**: Executes the validated SQL query against the SQLite database.
4.  **Answer Generation Agent**: Receives the results from the query runner and synthesizes a human-readable answer.

## Data Schema

The agent operates on a single table (derived from `world_bank_data_2025.csv`) with the following schema:

| Column Name               | Description                               |
| ------------------------- | ----------------------------------------- |
| `country_name`            | Extended country name the data refers to. |
| `country_id`              | 2-letter ID of the country.               |
| `year`                    | Year the data refers to.                  |
| `inflation`               | Inflation figures (CPI %).                |
| `gdp`                     | GDP figure.                               |
| `gdp_per_capita`          | GDP per capita numbers.                   |
| `unemployment_rate`       | Unemployment rate.                        |
| `interest_rate`           | Real interest rate.                       |
| `inflation_gdp_deflator`  | Inflation as GDP deflator.                |
| `gdp_growth`              | GDP growth as an annual percentage.       |
| `current_account_balance` | Current Account Balance as % of GDP.      |
| `government_expense`      | Government expense as % of GDP.           |
| `government_revenue`      | Government revenue as % of GDP.           |
| `tax_revenue`             | Tax revenue as % of GDP.                  |
| `gross_national_income`   | Gross national income in USD.             |
| `public_debt`             | Public debt as a percentage of GDP.       |

## Installation

This project uses `uv` for dependency management.

1.  **Install `uv`**:
    If you don't have `uv` installed, follow the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/):

2.  **Create a Virtual Environment**:
    ```bash
    uv venv
    ```
3.  **Activate the Virtual Environment**:
    - On macOS/Linux:
      ```bash
      source .venv/bin/activate
      ```
    - On Windows:
      ```bash
      .venv\\Scripts\\activate
      ```

4.  **Install Dependencies**:
    ```bash
    uv sync --all-groups
    ```

## Usage

To use the agent, you can either run it using the
[ADK CLI](https://google.github.io/adk-docs/get-started/quickstart/#run-your-agent)
or import the `root_agent` and call its `run_async` method.

Here is an example script:

```python
import asyncio

from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from injector import Binder, Injector, SingletonScope
from loguru import logger

from agent_sql_economic.agent import create_root_agent
from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import DataProvider, SQLiteDataProvider
from agent_sql_economic.module import MacroEconomicAgentDIModule


async def main():
    """Asynchronously runs the agent and prints the response."""
    config = AgentConfig(should_expand_intermediate_results=True)

    # Bind the config to the injector.
    def _bind_configuration(binder: Binder) -> None:
        binder.bind(AgentConfig, to=config, scope=SingletonScope)

    injector = Injector(modules=[_bind_configuration, MacroEconomicAgentDIModule])

    app_name = "macro-economic-app-test"
    user = "test-user"
    runner = Runner(
        app_name=app_name,
        agent=create_root_agent(injector),
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
    )
    session: Session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user,
    )

    # Prepare the user input.
    question = "What was the gdp and inflation for the Switzerland in 2021?"
    input_content = types.UserContent(question)

    async_iter = runner.run_async(
        user_id=user,
        session_id=session.id,
        new_message=input_content,
    )
    async for event in async_iter:
        if event.is_final_response() and event.content and event.content.parts:
            logger.info("Final response: {}", event.content.parts[0].text)

    # Close the connections to the DB to exit gracefully.
    data_provider = injector.get(DataProvider)
    if isinstance(data_provider, SQLiteDataProvider):
        await data_provider.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Save this script (e.g., `run_agent.py`) and execute it:

```bash
python -m run_agent
```

## Testing

The project uses `pytest` for testing. To run the test suite, execute the following command in the root directory:

```bash
pytest
```
