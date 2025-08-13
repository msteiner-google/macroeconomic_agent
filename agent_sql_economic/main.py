import asyncio

from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from injector import Binder, Injector, SingletonScope
from loguru import logger

from agent_sql_economic.agent import create_root_agent
from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.data_lookup import DataProvider, SQLiteDataProvider
from agent_sql_economic.module import MacroEconomicAgentDIModule


async def main():
    """Asynchronously runs the agent and prints the response."""
    config = AgentConfig(should_expand_intermediate_results=True)

    # Bind the config to the injector.
    def _bind_configuration(binder: Binder) -> None:
        binder.bind(AgentConfig, to=config, scope=SingletonScope)

    injector = Injector(modules=[_bind_configuration, MacroEconomicAgentDIModule])

    app_name = "macro-economic-app-test"
    user = "test-user"
    runner = Runner(
        app_name=app_name,
        agent=create_root_agent(injector),
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
    )
    session: Session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user,
    )

    # Prepare the user input.
    question = "What was the gdp and inflation for the Switzerland in 2021?"
    input_content = types.UserContent(question)

    async_iter = runner.run_async(
        user_id=user,
        session_id=session.id,
        new_message=input_content,
    )
    async for event in async_iter:
        if event.is_final_response() and event.content and event.content.parts:
            logger.info("Final response: {}", event.content.parts[0].text)

    # Close the connections to the DB to exit gracefully.
    data_provider = injector.get(DataProvider)
    if isinstance(data_provider, SQLiteDataProvider):
        await data_provider.close()


if __name__ == "__main__":
    asyncio.run(main())
