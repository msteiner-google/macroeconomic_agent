"""Agent that constructs the final answer."""

from textwrap import dedent

from google.adk.agents import Agent, LlmAgent
from injector import Injector
from loguru import logger

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import DataProvider


def get_answer_generation_agent(injector: Injector) -> Agent:
    """Generates the final answer."""
    configuration = injector.get(AgentConfig)
    data_provider = injector.get(DataProvider)
    instructions = dedent(f"""
    The following data has been created by running the SQL query derived from the user
    orginal question:

    ```json
    {{{configuration.sql_query_results_key}}}
    ```

    If the results are empty please comunicate that to the user and, if you are able to,
    try to guess what the problem with the orignal query was based on the schema:

    ```json
    {data_provider.get_schema()}
    ```

    If multiple rows are present in the results output the results in markdown format
    unless the user specifically specifies a different output format. Don't include
    the raw results in the query unless requested.
    """)
    logger.debug(instructions)
    return LlmAgent(
        name="AnswerAgent",
        model=configuration.model,
        instruction=instructions,
        description="Run the given SQL query.",
    )
