"""Module for dependency injection."""

from pathlib import Path

from injector import Module, multiprovider, provider, singleton
from loguru import logger

from agent_sql_economic.configuration import AgentConfig, MacroEconomicDataStorage
from agent_sql_economic.data_lookup import MacroEconomicDataProvider, SQLiteDataProvider


class MacroEconomicAgentDIModule(Module):
    """Dependency injection module."""

    @singleton
    @provider
    def _provide_lookup_table(  # noqa: PLR6301
        self, configuration: AgentConfig
    ) -> MacroEconomicDataProvider:
        match configuration.macroeconomic_data_location:
            case MacroEconomicDataStorage.SQLITE_IN_MEMORY:
                data_path = Path().absolute() / "data/world_bank_data_2025.csv"
                logger.info("Using data for SQLITE_IN_MEMORY at:", str(data_path))
                return SQLiteDataProvider(csv_data=data_path)
            case _:
                raise NotImplementedError()
