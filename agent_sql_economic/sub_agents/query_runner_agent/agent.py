"""Agent that runs the query."""

from google.adk.agents import Agent, LlmAgent
from injector import Injector

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import MacroEconomicDataProvider


def get_query_runner_agent(injector: Injector) -> Agent:
    """Runs the SQL query."""
    configuration = injector.get(AgentConfig)
    data_provider = injector.get(MacroEconomicDataProvider)
    return LlmAgent(
        name="QueryRunnerAgent",
        model=configuration.model,
        # Change 3: Improved instruction, correctly using state key injection
        instruction="""
    You run the {sql_query}.
    """,
        description="Run the given SQL query.",
        output_key="raw_data",  # Stores output in state['review_comments']
        tools=[data_provider.fetch_data],
    )
