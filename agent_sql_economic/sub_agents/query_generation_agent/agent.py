"""Sub agent that generates the query."""

import time
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from injector import Injector
from loguru import logger

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import MacroEconomicDataProvider


def _get_llm_query_generator_agent(
    configuration: AgentConfig, data_provider: MacroEconomicDataProvider
) -> LlmAgent:
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


class _CustomQueryGeneratorAgent(BaseAgent):
    data_provider: MacroEconomicDataProvider
    agent_config: AgentConfig
    llm_agent: LlmAgent

    def __init__(
        self, agent_config: AgentConfig, data_provider: MacroEconomicDataProvider
    ) -> None:
        super().__init__(
            name="QueryRunnerAgent",
            data_provider=data_provider,
            agent_config=agent_config,
            llm_agent=_get_llm_query_generator_agent(
                configuration=agent_config, data_provider=data_provider
            ),
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.info("CTX: {}", ctx.session.state)
        final_response: str | None = ""
        async for event in self.llm_agent.run_async(ctx):
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text
                logger.info(
                    "Potential final response from [{}]: {}",
                    event.author,
                    final_response,
                )
                break

        state_changes = {self.agent_config.sql_query_key: final_response}
        actions_with_update = EventActions(state_delta=state_changes)

        current_time = time.time()

        system_event = Event(
            invocation_id="query_generator",
            author=self.name,
            actions=actions_with_update,
            timestamp=current_time,
        )
        await ctx.session_service.append_event(ctx.session, system_event)

        yield Event(author=self.name)


def get_query_generation_agent(injector: Injector) -> BaseAgent:
    """Generates the SQL query."""
    configuration = injector.get(AgentConfig)
    data_provider = injector.get(MacroEconomicDataProvider)
    return _CustomQueryGeneratorAgent(
        agent_config=configuration, data_provider=data_provider
    )
