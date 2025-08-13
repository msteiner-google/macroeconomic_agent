"""Module with data providers definitions."""

import sqlite3
from abc import ABC, abstractmethod
from asyncio import Lock
from collections.abc import Collection
from pathlib import Path

import aiosqlite
import pandas as pd
from loguru import logger
from pydantic import BaseModel


class DataSource(BaseModel):
    """Defines a datasource."""

    table_name: str
    table_schema: dict[str, tuple[str, str]]


class DataProvider(ABC):
    """ABC for a MacroEconomicDataProvider."""

    @property
    @abstractmethod
    def dialect(self) -> str:
        """The SQL dialect to use."""

    @property
    @abstractmethod
    def data_sources(self) -> Collection[DataSource]:
        """DataSources available."""

    @abstractmethod
    async def fetch_data(self, query: str) -> list[dict[str, str | float | int]]:
        """Given a query retrieve the data."""
        ...

    @abstractmethod
    async def validate_query(self, sql_query: str) -> bool:
        """Checks if the given sql query is valid or not."""
        ...

    def get_schema(self) -> str:
        """Schema for the data."""
        return "\n".join([
            source.model_dump_json(indent=2) for source in self.data_sources
        ])


class SQLiteDataProvider(DataProvider):
    """Provider for macro economic data from a SQLite database."""

    def __init__(
        self,
        csv_data: Path,
        db_path: str | Path | None = None,
    ) -> None:
        """Initializes the data provider and loads data from a CSV file.

        If db_path is None, a shareable in-memory database is used.
        Otherwise, it connects to the file specified by db_path.
        """
        if db_path is None:
            # Use a shareable in-memory database URI
            self.db_path = "file::memory:?cache=shared"
        else:
            self.db_path = db_path

        self._load_data_from_csv(csv_data)
        self.db: aiosqlite.Connection | None = None
        self.lock: Lock = Lock()

    def _load_data_from_csv(self, csv_path: Path) -> None:
        """Loads data from the given CSV file into the SQLite database."""
        table_name = csv_path.stem  # Use the CSV filename as the table name
        logger.info("SQLITE Table name: {}", table_name)
        df = pd.read_csv(csv_path)

        # Use standard sqlite3 for this synchronous operation
        with sqlite3.connect(self.db_path, uri=True) as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)

    @property
    def dialect(self) -> str:
        """The SQL dialect to use, which is 'sqlite'."""
        return "sqlite"

    @property
    def data_sources(self) -> Collection[DataSource]:  # noqa: D102
        return [
            DataSource(
                table_name="world_bank_data_2025",
                table_schema={
                    "country_name": (
                        "Extendend country name the data refers to",
                        "STRING",
                    ),
                    "country_id": ("2 letters id of the country", "STRING"),
                    "year": ("Year the data refers to.", "INTEGER"),
                    "inflation": ("Inflation figures (CPI %).", "FLOAT"),
                    "gdp": ("GDP figure.", "FLOAT"),
                    "gdp_per_capita": ("GDP per capita numbers.", "FLOAT"),
                    "unemployment_rate": ("Unemployment rate.", "FLOAT"),
                    "interest_rate": ("Real interenest rate.", "FLOAT"),
                    "inflation_gdp_deflator": ("Inflation as GDP deflator.", "FLOAT"),
                    "gdp_growth": ("GDP growth as annual percentage.", "FLOAT"),
                    "current_account_balance": (
                        "Current Account Balance as % of GDP.",
                        "FLOAT",
                    ),
                    "government_expense": ("Government expense as % of GDP.", "FLOAT"),
                    "government_revenue": ("Government revenue as % of GDP.", "FLOAT"),
                    "tax_revenue": ("Tax revenue as % of GDP.", "FLOAT"),
                    "gross_national_income": ("Gross national income in USD.", "FLOAT"),
                    "public_debt": ("Public debt as percent of GDP.", "FLOAT"),
                },
            )
        ]

    async def _get_conn(self) -> aiosqlite.Connection:
        """Get the database connection, creating it if it doesn't exist."""
        async with self.lock:
            if self.db is None:
                self.db = await aiosqlite.connect(self.db_path, uri=True)
            return self.db

    async def close(self) -> None:
        """Closes the database connection."""
        async with self.lock:
            if self.db:
                await self.db.close()
                self.db = None

    async def fetch_data(self, query: str) -> list[dict[str, str | float | int]]:
        """Given a query, retrieve data from the SQLite database."""
        conn = await self._get_conn()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def validate_query(self, sql_query: str) -> bool:
        """Checks if the given sql query is valid or not."""
        logger.info("SQL_QUERY: {}", sql_query)
        explain_query = f"EXPLAIN {sql_query}"
        try:
            conn = await self._get_conn()
            async with conn.execute(explain_query):
                return True
        except sqlite3.Error:
            return False
