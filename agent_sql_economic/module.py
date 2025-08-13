"""Module for dependency injection."""

from pathlib import Path

from injector import Module, provider, singleton
from loguru import logger

from agent_sql_economic.configuration import AgentConfig, MacroEconomicDataStorage
from agent_sql_economic.data_lookup import DataProvider, SQLiteDataProvider


class MacroEconomicAgentDIModule(Module):
    """Dependency injection module."""

    @singleton
    @provider
    def _provide_lookup_table(  # noqa: PLR6301
        self, configuration: AgentConfig
    ) -> DataProvider:
        match configuration.macroeconomic_data_location:
            case MacroEconomicDataStorage.SQLITE:
                data_path = Path().absolute() / "data/world_bank_data_2025.csv"
                db_path = Path().absolute() / "data/db.sqlite"
                logger.info("Using data for SQLITE_IN_MEMORY at:", str(data_path))
                return SQLiteDataProvider(csv_data=data_path, db_path=db_path)
            case _:
                raise NotImplementedError()
