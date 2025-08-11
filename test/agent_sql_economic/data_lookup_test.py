"""Data lookup tests."""

from pathlib import Path

import pandas as pd
import pytest

from agent_sql_economic.data_lookup import SQLiteDataProvider


@pytest.fixture
def data_provider(tmp_path: Path) -> SQLiteDataProvider:
    """Fixture to create a SQLiteDataProvider with dummy data."""
    csv_path = tmp_path / "test_data.csv"
    data = {"country_name": ["Testland"], "year": [2023], "gdp": [1000.0]}
    pd.DataFrame(data).to_csv(csv_path, index=False)

    # Use a file-based DB for test isolation
    db_path = tmp_path / "test.db"
    return SQLiteDataProvider(csv_data=csv_path, db_path=db_path)


@pytest.mark.asyncio
async def test_validate_query_valid(data_provider: SQLiteDataProvider) -> None:
    """Test that a valid query returns True."""
    query = "SELECT * FROM test_data"
    is_valid = await data_provider.validate_query(query)
    assert is_valid is True


@pytest.mark.asyncio
async def test_validate_query_invalid_syntax(data_provider: SQLiteDataProvider) -> None:
    """Test that a query with invalid syntax returns False."""
    query = "SELEC * FROM test_data"
    is_valid = await data_provider.validate_query(query)
    assert is_valid is False


@pytest.mark.asyncio
async def test_validate_query_nonexistent_table(
    data_provider: SQLiteDataProvider,
) -> None:
    """Test that a query on a non-existent table returns False."""
    query = "SELECT * FROM non_existent_table"
    is_valid = await data_provider.validate_query(query)
    assert is_valid is False


@pytest.mark.asyncio
async def test_validate_query_nonexistent_column(
    data_provider: SQLiteDataProvider,
) -> None:
    """Test that a query on a non-existent column returns False."""
    query = "SELECT non_existent_column FROM test_data"
    is_valid = await data_provider.validate_query(query)
    assert is_valid is False
