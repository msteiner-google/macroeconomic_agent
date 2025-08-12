"""Sub agent that generates the query."""

from google.adk.agents import Agent, LlmAgent
from injector import Injector

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import MacroEconomicDataProvider


def get_query_generation_agent(injector: Injector) -> Agent:
    """Generates the SQL query."""
    configuration = injector.get(AgentConfig)
    data_provider = injector.get(MacroEconomicDataProvider)
    return LlmAgent(
        name="QueryGeneratorAgent",
        model=configuration.model,
        # Change 3: Improved instruction, correctly using state key injection
        instruction=f"""
    You are an experencied data analyst. Your task is to come up with a SQL
    query using the {data_provider.dialect} SQL dialect.

    The query should be used to anser the {{query?}} provided by the business users.
    The table name is "world_bank_data_2025" and it has the following schema where
    the key is the column name and the value it is the description of the column:

    ```json
    {data_provider.get_schema()}
    ```

    Be sure to use correct column names.

    """,
        description="Generates a SQL query.",
        output_key=configuration.sql_query_key,
    )
