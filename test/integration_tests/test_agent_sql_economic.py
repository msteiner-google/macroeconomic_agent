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
from agent_sql_economic.data_lookup import DataProvider, SQLiteDataProvider
from agent_sql_economic.module import MacroEconomicAgentDIModule


@pytest_asyncio.fixture
async def runner(config: AgentConfig) -> AsyncIterator[Runner]:  # noqa: D103
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
    data_provider = injector.get(DataProvider)
    if isinstance(data_provider, SQLiteDataProvider):
        await data_provider.close()


@pytest_asyncio.fixture
async def config() -> AgentConfig:  # noqa: D103, RUF029
    return AgentConfig(should_expand_intermediate_results=True)


async def _invoke(question: str, runner: Runner) -> tuple[list[Event], Session]:
    user = "test-user"

    session = await runner.session_service.create_session(
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
async def test_sql_bot_answers_to_pleasantry(runner: Runner) -> None:  # noqa: D103
    question = "hi"

    events, _ = await _invoke(question=question, runner=runner)
    assert events, "Expected at least one event"

    content = events[-1].content
    assert content, "Expected at least one content"

    text = "\n\n".join(part.text for part in content.parts or [] if part.text)
    assert text


_valid_queries = [
    "What is the country with the lowest GDP per capita in 2022?",
    "What are the 10 countries with the highest inflation in 2020?",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("question", _valid_queries)
async def test_sql_bot_generate_simple_valid_queries(  # noqa: D103
    runner: Runner, config: AgentConfig, question: str
) -> None:
    events, _ = await _invoke(question=question, runner=runner)
    assert events, "Expected at least one event"

    # Check that the query was created
    assert any(config.sql_query_key in e.actions.state_delta for e in events)

    # Checks that the query was valid
    assert any(config.query_validation_key in e.actions.state_delta for e in events)

    # Check that the query passed validation.
    assert any(
        config.query_validation_key in e.actions.state_delta
        and e.actions.state_delta[config.query_validation_key]
        for e in events
    )

    # Checks that the query results are not empty. I.e. there is at least
    # 1 row and 1 column.
    results_found = False
    for e in events:
        if config.sql_query_results_key in e.actions.state_delta:
            results_found = True

            json_res = json.loads(
                str(e.actions.state_delta[config.sql_query_results_key])
            )
            assert len(json_res) > 0
            assert len(json_res[0].keys()) > 0
    assert results_found
