"""Actual agent implementation for the agent that performs the query validation."""

from google.adk.agents import Agent, LlmAgent
from injector import Injector

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import MacroEconomicDataProvider


def get_query_validation_agent(injector: Injector) -> Agent:
    """Validates the SQL query."""
    configuration = injector.get(AgentConfig)
    data_provider = injector.get(MacroEconomicDataProvider)
    return LlmAgent(
        name="QueryValidatorAgent",
        model=configuration.model,
        # Change 3: Improved instruction, correctly using state key injection
        instruction=f"""
        You are an expert SQL user. Given the following

        ```sql
        {{sql_query}}
        ```

        that targets a table called `world_bank_data_2025` that has the following
        schema:

        ```json
        {data_provider.get_schema()}
        ```
        you tell whether or not the query is valid.
        """,
        description="Validate a given SQL query.",
        output_key="is_query_valid",  # Stores output in state['review_comments']
        tools=[data_provider.validate_query()],
    )
