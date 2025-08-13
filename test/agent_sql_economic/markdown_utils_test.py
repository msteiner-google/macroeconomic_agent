"""Tests for markdown_utils."""

import pytest

from agent_sql_economic.markdown_utils import extract_sql_from_markdown


@pytest.mark.parametrize(
    ("markdown_string", "expected_sql"),
    [
        (
            "```sql\nSELECT * FROM my_table;\n```",
            "SELECT * FROM my_table;",
        ),
        (
            "SELECT * FROM another_table;",
            "SELECT * FROM another_table;",
        ),
        ("", ""),
        ("```sql\n```", ""),
        (
            "  ```sql\nSELECT 1;\n```  ",
            "SELECT 1;",
        ),
    ],
)
def test_extract_sql_from_markdown(markdown_string: str, expected_sql: str) -> None:
    """Tests that SQL is correctly extracted from a markdown string."""
    assert extract_sql_from_markdown(markdown_string) == expected_sql
