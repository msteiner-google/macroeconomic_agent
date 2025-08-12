"""Utils for working with raw markdown."""


def extract_sql_from_markdown(markdown_string: str) -> str:
    """Removes Markdown fences from a SQL code block string."""
    lines = markdown_string.strip().split("\n")
    # Slice the list to exclude the first and last lines
    sql_lines = lines[1:-1]
    return "\n".join(sql_lines)
