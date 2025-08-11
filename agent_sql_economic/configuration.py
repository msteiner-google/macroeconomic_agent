"""Configuration module."""

from enum import StrEnum

from pydantic import BaseModel, Field


class MacroEconomicDataStorage(StrEnum):
    """Location of the macroeconomic data."""

    SQLITE_IN_MEMORY = "in_memory"
    BIG_QUERY = "big_query"


class AgentConfig(BaseModel):
    """Global configuration of the agent."""

    macroeconomic_data_location: MacroEconomicDataStorage = Field(
        default=MacroEconomicDataStorage.SQLITE_IN_MEMORY
    )
