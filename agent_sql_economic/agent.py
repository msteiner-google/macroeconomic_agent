"""Main agent."""

from google.adk.agents import SequentialAgent
from injector import Binder, Injector, SingletonScope

from agent_sql_economic.configuration import AgentConfig
from agent_sql_economic.module import MacroEconomicAgentDIModule
from agent_sql_economic.sub_agents.answer_generation_agent.agent import (
    get_answer_generation_agent,
)
from agent_sql_economic.sub_agents.query_generation_agent import (
    get_query_generation_agent,
)
from agent_sql_economic.sub_agents.query_runner_agent.agent import (
    get_query_runner_agent,
)
from agent_sql_economic.sub_agents.query_validation_agent import (
    get_query_validation_agent,
)

configuration: AgentConfig = AgentConfig(should_expand_intermediate_results=False)


def _bind_configuration(binder: Binder) -> None:
    binder.bind(AgentConfig, to=configuration, scope=SingletonScope)


def create_root_agent(injector: Injector) -> SequentialAgent:
    """Creates the root sequential agent with all its sub-agents."""
    query_generation_agent = get_query_generation_agent(injector)
    query_validation_agent = get_query_validation_agent(injector)
    query_runner_agent = get_query_runner_agent(injector)
    answer_agent = get_answer_generation_agent(injector)

    return SequentialAgent(
        name="NL2SQLAgent",
        sub_agents=[
            query_generation_agent,
            query_validation_agent,
            query_runner_agent,
            answer_agent,
        ],
        description="""
        Generates and validates a given
        query from a natural language question.""",
    )


injector = Injector(modules=[_bind_configuration, MacroEconomicAgentDIModule])
root_agent = create_root_agent(injector)
