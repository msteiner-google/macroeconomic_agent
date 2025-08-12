"""Configuration module."""

from enum import StrEnum

from pydantic import BaseModel, Field


class MacroEconomicDataStorage(StrEnum):
    """Location of the macroeconomic data."""

    SQLITE = "in_memory"
    BIG_QUERY = "big_query"


class AgentConfig(BaseModel):
    """Global configuration of the agent."""

    agent_name: str = Field(default="Macroeconomic agent.")
    model: str = Field(default="gemini-2.5-flash")

    should_expand_intermediate_results: bool = False

    macroeconomic_data_location: MacroEconomicDataStorage = Field(
        default=MacroEconomicDataStorage.SQLITE
    )
    query_validation_key: str = "is_query_valid"
    sql_query_key: str = "sql_query"
    sql_query_results_key: str = "query_results"
