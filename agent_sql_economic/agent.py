"""Main agent."""

from google.adk.agents import Agent, LlmAgent, SequentialAgent
from injector import Binder, Injector, SingletonScope

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import MacroEconomicDataProvider
from agent_sql_economic.module import MacroEconomicAgentDIModule

configuration: AgentConfig = AgentConfig()


def _bind_configuration(binder: Binder) -> None:
    binder.bind(AgentConfig, to=configuration, scope=SingletonScope)


injector = Injector(modules=[_bind_configuration, MacroEconomicAgentDIModule])


data_provider: MacroEconomicDataProvider = injector.get(MacroEconomicDataProvider)

query_generation_agent = LlmAgent(
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
    output_key="sql_query",  # Stores output in state['review_comments']
)

query_validation_agent = LlmAgent(
    name="QueryValidatorAgent",
    model=configuration.model,
    # Change 3: Improved instruction, correctly using state key injection
    instruction=f"""
    You are an expert SQL user. Given the following

    ```sql
    {{sql_query}}
    ```

    that targets a table called `world_bank_data_2025` that has the following schema:

    ```json
    {data_provider.get_schema()}
    ```
    you tell whether or not the query is valid.
    """,
    description="Validate a given SQL query.",
    output_key="is_query_valid",  # Stores output in state['review_comments']
    tools=[data_provider.validate_query()],
)

query_runner_agent = LlmAgent(
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
answer_agent = LlmAgent(
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

root_agent = SequentialAgent(
    name="MacroEconomicSQLAgent",
    sub_agents=[
        query_generation_agent,
        query_validation_agent,
        query_runner_agent,
        answer_agent,
    ],
    description="Generates and validates a given query from a natural language question.",
    # The agents will run in the order provided: Writer -> Reviewer -> Refactorer
)
