"""Integration tests for the Macro-Economic SQL Agent."""

import os
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, patch, Mock

import pandas as pd
import pytest
import pytest_asyncio
from google.adk.agents import Agent
from google.adk.agents.invocation_context import (
    InvocationContext,
    new_invocation_context_id,
)
from google.adk.agents.run_config import RunConfig
from google.adk.sessions.state import State
from google.adk.sessions.session import Session
from google.adk.sessions.base_session_service import BaseSessionService
from injector import Injector

from agent_sql_economic.agent import (
    _bind_configuration,
    get_answer_generation_agent,
    get_query_generation_agent,
    get_query_runner_agent,
    get_query_validation_agent,
    root_agent,
)
from agent_sql_economic.data_lookup import SQLiteDataProvider
from agent_sql_economic.module import MacroEconomicAgentDIModule


@pytest_asyncio.fixture
async def data_provider(tmp_path: Path) -> AsyncIterator[SQLiteDataProvider]:
    """Fixture to create a SQLiteDataProvider with test data."""
    csv_path = tmp_path / "test_data.csv"
    data = {
        "country_name": ["Testland", "Testland", "Anotherland"],
        "year": [2023, 2024, 2024],
        "gdp": [1000.0, 1100.0, 1500.0],
        "inflation": [2.0, 2.5, 3.0],
    }
    pd.DataFrame(data).to_csv(csv_path, index=False)

    db_path = tmp_path / "test.db"
    provider = SQLiteDataProvider(csv_data=csv_path, db_path=db_path)
    yield provider
    await provider.close()


@pytest_asyncio.fixture
def test_agent(data_provider: SQLiteDataProvider) -> Agent:
    """Fixture to create a test agent with a mocked data provider."""
    os.environ["GOOGLE_API_KEY"] = "test"

    def _bind_test_module(binder):
        binder.bind(SQLiteDataProvider, to=data_provider)

    injector = Injector(
        modules=[_bind_configuration, MacroEconomicAgentDIModule, _bind_test_module]
    )

    with patch(
        "google.adk.models.registry.LLMRegistry.new_llm"
    ) as mock_new_llm:
        mock_model = AsyncMock()
        mock_model.generate_content_async.side_effect = [
            # 1. Query Generation
            "SELECT gdp FROM test_data WHERE country_name = 'Testland' AND year = 2023",
            # 2. Answer Generation
            "The GDP for Testland in 2023 was 1000.0.",
            # 3. Query Generation (Multi-metric)
            "SELECT gdp, inflation FROM test_data WHERE country_name = 'Testland' AND year = 2024",
            # 4. Answer Generation (Multi-metric)
            "The GDP for Testland in 2024 was 1100.0 and inflation was 2.5.",
            # 5. Query Generation (WHERE clause)
            "SELECT gdp FROM test_data WHERE country_name = 'Anotherland'",
            # 6. Answer Generation (WHERE clause)
            "The GDP for Anotherland is 1500.0.",
            # 7. Query Generation (Invalid)
            "SELECT gdp FROM non_existent_table",
        ]
        mock_new_llm.return_value = mock_model

        # Re-create the agent using the test injector
        root_agent.sub_agents = [
            get_query_generation_agent(injector),
            get_query_validation_agent(injector),
            get_query_runner_agent(injector),
            get_answer_generation_agent(injector),
        ]
        return root_agent


async def run_agent_and_get_response(agent: Agent, question: str) -> str:
    """Runs the agent and returns the final response."""
    session = Session(
        id="test_session",
        app_name="test_app",
        user_id="test_user",
        state={"question": question},
    )
    session_service = Mock(spec=BaseSessionService)
    context = InvocationContext(
        invocation_id=new_invocation_context_id(),
        agent=agent,
        session=session,
        session_service=session_service,
        run_config=RunConfig(),
    )

    response = ""
    async for event in agent.run_async(context):
        if event.is_final_response() and event.content and event.content.parts:
            response = "".join(part.text for part in event.content.parts)
            break
    return response


@pytest.mark.asyncio
async def test_agent_single_metric(test_agent: Agent):
    """Test the agent with a single-metric question."""
    question = "What was the GDP of Testland in 2023?"
    response = await run_agent_and_get_response(test_agent, question)
    assert "1000.0" in response


@pytest.mark.asyncio
async def test_agent_multi_metric(test_agent: Agent):
    """Test the agent with a multi-metric question."""
    question = "What was the GDP and inflation for Testland in 2024?"
    response = await run_agent_and_get_response(test_agent, question)
    assert "1100.0" in response
    assert "2.5" in response


@pytest.mark.asyncio
async def test_agent_with_where_clause(test_agent: Agent):
    """Test the agent with a question that requires a WHERE clause."""
    question = "What is the GDP of Anotherland?"
    response = await run_agent_and_get_response(test_agent, question)
    assert "1500.0" in response


@pytest.mark.asyncio
async def test_agent_invalid_query(test_agent: Agent):
    """Test the agent with a question that generates an invalid query."""
    question = "What is the GDP from a non-existent table?"
    with pytest.raises(ValueError, match="Invalid query"):
        await run_agent_and_get_response(test_agent, question)
