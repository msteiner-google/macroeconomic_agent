"""Agent that constructs the final answer."""

from google.adk.agents import Agent, LlmAgent
from injector import Injector

from agent_sql_economic.configuration import AgentConfig


def get_answer_generation_agent(injector: Injector) -> Agent:
    """Generates the final answer."""
    configuration = injector.get(AgentConfig)
    return LlmAgent(
        name="AnswerAgent",
        model=configuration.model,
        instruction=f"""
    The following data has been created by running the SQL query derived from the user
    orginal question:

    ```json
    {configuration.sql_query_results_key}
    ```

    Use it to answer the original question.
    """,
        description="Run the given SQL query.",
    )
