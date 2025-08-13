"""Actual agent implementation for the agent that performs the query validation."""

import time
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from injector import Injector
from loguru import logger

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import DataProvider
from agent_sql_economic.markdown_utils import extract_sql_from_markdown


class _CustomQueryValidationAgent(BaseAgent):
    data_provider: DataProvider
    agent_config: AgentConfig

    def __init__(self, agent_config: AgentConfig, data_provider: DataProvider) -> None:
        super().__init__(
            name="QueryValidationAgent",
            data_provider=data_provider,
            agent_config=agent_config,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.info("CTX: {}", ctx.session.state)
        sql_query: str = ctx.session.state[self.agent_config.sql_query_key]
        sql_query = extract_sql_from_markdown(sql_query)
        result = await self.data_provider.validate_query(sql_query)

        state_changes = {
            self.agent_config.query_validation_key: result,
            self.agent_config.sql_query_key: ctx.session.state.get(
                self.agent_config.sql_query_key
            ),
        }
        actions_with_update = EventActions(state_delta=state_changes)

        current_time = time.time()

        system_event = Event(
            invocation_id="query_validation",
            author=self.name,  # Or 'agent', 'tool' etc.
            actions=actions_with_update,
            timestamp=current_time,
        )
        await ctx.session_service.append_event(ctx.session, system_event)

        if self.agent_config.should_expand_intermediate_results:
            yield system_event
        else:
            yield Event(author=self.name)


def get_query_validation_agent(injector: Injector) -> BaseAgent:
    """Validates the SQL query."""
    configuration = injector.get(AgentConfig)
    data_provider = injector.get(DataProvider)
    return _CustomQueryValidationAgent(
        agent_config=configuration, data_provider=data_provider
    )
