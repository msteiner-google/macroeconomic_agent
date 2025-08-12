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
        # Change 3: Improved instruction, correctly using state key injection
        instruction="""
    Reply to the user question.

    The context data you have access to is:

    {raw_data}
    """,
        description="Run the given SQL query.",
    )
