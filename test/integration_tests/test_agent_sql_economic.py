"""Integration tests for the Macro-Economic SQL Agent."""

import json
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events.event import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from injector import Binder, Injector, SingletonScope

from agent_sql_economic.agent import create_root_agent
from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import MacroEconomicDataProvider, SQLiteDataProvider
from agent_sql_economic.module import MacroEconomicAgentDIModule


@pytest_asyncio.fixture
async def runner(config: AgentConfig) -> AsyncIterator[Runner]:
    def _bind_configuration(binder: Binder) -> None:
        binder.bind(AgentConfig, to=config, scope=SingletonScope)

    injector = Injector(modules=[_bind_configuration, MacroEconomicAgentDIModule])
    yield Runner(
        app_name="test",
        agent=create_root_agent(injector),
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
    )
    # Once the tests are over, kill the `aiosqlite` connections so that the
    # event loop can exit.
    data_provider = injector.get(MacroEconomicDataProvider)
    if isinstance(data_provider, SQLiteDataProvider):
        await data_provider.close()


@pytest_asyncio.fixture
async def config() -> AgentConfig:
    return AgentConfig(should_expand_intermediate_results=True)


async def _invoke(question: str, runner: Runner) -> tuple[list[Event], Session]:
    user = "test-user"

    assert isinstance(runner.session_service, InMemorySessionService)
    session = runner.session_service.create_session_sync(
        app_name=runner.app_name,
        user_id=user,
    )

    input_content = types.UserContent(question)

    async_iter = runner.run_async(
        user_id=user,
        session_id=session.id,
        new_message=input_content,
    )
    return [event async for event in async_iter if event is not None], session


@pytest.mark.asyncio
async def test_sql_bot_answers_to_pleasantry(runner: Runner) -> None:
    question = "hi"

    events, _ = await _invoke(question=question, runner=runner)
    assert events, "Expected at least one event"

    content = events[-1].content
    assert content, "Expected at least one content"

    text = "\n\n".join(part.text for part in content.parts or [] if part.text)
    assert text


@pytest.mark.asyncio
async def test_sql_bot_generate_simple_valid_queries(
    runner: Runner, config: AgentConfig
) -> None:
    question = "What is the country with the lowest GDP per capita in 2022?"

    events, _ = await _invoke(question=question, runner=runner)
    assert events, "Expected at least one event"

    # Check that the query was created
    assert config.sql_query_key in events[0].actions.state_delta

    # Checks that the query was valid
    assert config.query_validation_key in events[1].actions.state_delta
    # Check that the query passed validation.
    assert events[1].actions.state_delta[config.query_validation_key]

    # Checks that the query results are not empty. I.e. there is at least
    # 1 row and 1 column.
    assert config.sql_query_results_key in events[2].actions.state_delta
    json_res = json.loads(
        str(events[2].actions.state_delta[config.sql_query_results_key])
    )
    assert len(json_res) > 0
    assert len(json_res[0].keys()) > 0
