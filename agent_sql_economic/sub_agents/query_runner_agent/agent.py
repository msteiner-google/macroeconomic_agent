"""Agent that runs the query."""

import json
import time
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from injector import Injector
from loguru import logger

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import MacroEconomicDataProvider
from agent_sql_economic.markdown_utils import extract_sql_from_markdown


class _CustomQueryRunnerAgent(BaseAgent):
    data_provider: MacroEconomicDataProvider
    agent_config: AgentConfig

    def __init__(
        self, agent_config: AgentConfig, data_provider: MacroEconomicDataProvider
    ) -> None:
        super().__init__(
            name="QueryRunnerAgent",
            data_provider=data_provider,
            agent_config=agent_config,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.info("CTX: {}", ctx.session.state)
        sql_query: str = ctx.session.state[self.agent_config.sql_query_key]
        sql_query = extract_sql_from_markdown(sql_query)
        results = await self.data_provider.fetch_data(sql_query)

        state_changes = {
            self.agent_config.sql_query_results_key: json.dumps(results, indent=2),
            self.agent_config.sql_query_key: ctx.session.state.get(
                self.agent_config.sql_query_key
            ),
        }
        actions_with_update = EventActions(state_delta=state_changes)

        current_time = time.time()

        system_event = Event(
            invocation_id="query_runner",
            author=self.name,
            actions=actions_with_update,
            timestamp=current_time,
        )
        await ctx.session_service.append_event(ctx.session, system_event)

        yield Event(author=self.name)


def get_query_runner_agent(injector: Injector) -> BaseAgent:
    """Generates the SQL query."""
    configuration = injector.get(AgentConfig)
    data_provider = injector.get(MacroEconomicDataProvider)
    return _CustomQueryRunnerAgent(
        agent_config=configuration, data_provider=data_provider
    )
