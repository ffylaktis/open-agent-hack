"""Data layer: one tool, run_sql(), that sends a single SQL statement to
Zetaris over its REST API and returns the rows.

Zetaris is the center of the build — ground every answer in it.
"""
import os
import uuid
import requests

ZETARIS_REST_URL = os.environ.get("ZETARIS_REST_URL", "http://localhost:8888/api/v1.0")
ZETARIS_ORG_ID = os.environ.get("ZETARIS_ORG_ID", "1")
ZETARIS_API_KEY = os.environ.get("ZETARIS_API_KEY", "")


def run_sql(sql: str, limit: int = 100) -> list:
    """Run one SQL statement against Zetaris and return its rows.

    Send one complete statement at a time (Lightning SQL). Never print the
    API key.
    """
    response = requests.post(
        ZETARIS_REST_URL.rstrip("/") + "/sql-editor/sqls/run",
        headers={
            "Authorization": "Bearer " + ZETARIS_API_KEY,
            "X-Org-ID": ZETARIS_ORG_ID,
            "X-Request-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
        },
        json={
            "queryId": str(uuid.uuid4()),
            "sql": sql,
            "source": "SqlEditor",
            "limit": limit,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("data", [])


# Tool schema the model sees (OpenAI tool-calling format).
RUN_SQL_TOOL = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": (
            "Run a single read-only SQL (Lightning SQL) statement against the "
            "Zetaris data platform and return the resulting rows."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "One complete SQL statement."}
            },
            "required": ["sql"],
        },
    },
}
