"""Module with data providers definitions."""

import json
import sqlite3
from abc import ABC, abstractmethod
from asyncio import Lock
from pathlib import Path

import aiosqlite
import pandas as pd
from google.adk.tools import FunctionTool
from loguru import logger


class MacroEconomicDataProvider(ABC):
    """ABC for a MacroEconomicDataProvider."""

    @property
    @abstractmethod
    def dialect(self) -> str:
        """The SQL dialect to use."""
        ...

    @abstractmethod
    async def fetch_data(self, query: str) -> list[dict[str, str | float | int]]:
        """Given a query retrieve the data."""
        ...

    @abstractmethod
    def validate_query(self) -> FunctionTool:
        """Checks if the given sql query is valid or not."""
        ...

    @staticmethod
    def get_schema() -> str:
        """Schema for the data."""
        return json.dumps(
            {
                "country_name": "Extendend country name the data refers to",
                "country_id": "2 letters id of the country",
                "year": "Year the data refers to.",
                "inflation": "Inflation figures (CPI %).",
                "gdp": "GDP figure.",
                "gdp_per_capita": "GDP per capita numbers.",
                "unemployment_rate": "Unemployment rate.",
                "interest_rate": "Real interenest rate.",
                "inflation_gdp_deflator": "Inflation as GDP deflator.",
                "gdp_growth": "GDP growth as annual percentage.",
                "current_account_balance": "Current Account Balance as % of GDP.",
                "government_expense": "Government expense as % of GDP.",
                "government_revenue": "Government revenue as % of GDP.",
                "tax_revenue": "Tax revenue as % of GDP.",
                "gross_national_income": "Gross national income in USD.",
                "public_debt": "Public debt as percent of GDP.",
            },
            indent=2,
        )


class SQLiteDataProvider(MacroEconomicDataProvider):
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

    async def fetch_data(self, query: str) -> list[dict[str, str | float | int]]:
        """Given a query, retrieve data from the SQLite database."""
        async with self.lock:
            if self.db is None:
                self.db = await aiosqlite.connect(self.db_path, uri=True)
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    def validate_query(self) -> FunctionTool:
        """Checks if the given sql query is valid or not."""

        # Using EXPLAIN is a lightweight way to ask the database to parse
        # and plan the query without executing it. If the syntax is invalid,
        # it will raise an error.
        @FunctionTool
        async def helper(sql_query: str) -> dict[str, bool]:
            logger.info("SQL_QUERY: {}", sql_query)
            explain_query = f"EXPLAIN {sql_query}"

            async with self.lock:
                if self.db is None:
                    self.db = await aiosqlite.connect(self.db_path, uri=True)
            try:
                async with aiosqlite.connect(self.db_path, uri=True) as db:
                    await db.execute(explain_query)
                return {"is_query_valid": True}  # noqa: TRY300
            except sqlite3.Error:
                return {"is_query_valid": False}

        return helper
