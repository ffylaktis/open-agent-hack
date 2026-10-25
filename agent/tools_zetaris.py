"""Data-layer tools: safe, read-only access to Zetaris over REST.

Every agent reaches data only through here. Rules enforced (per Zetaris AGENTS.md
+ PRD safety): one statement per call, no trailing ';', read-only verbs only,
a LIMIT is injected on bare SELECT/WITH, qualified names like `ctgov.trials`.
"""
import os
import re
import uuid
import requests

ZETARIS_REST_URL = os.environ.get("ZETARIS_REST_URL", "http://localhost:8888/api/v1.0")
ZETARIS_ORG_ID = os.environ.get("ZETARIS_ORG_ID", "1")
ZETARIS_API_KEY = os.environ.get("ZETARIS_API_KEY", "")
SQL_ROW_LIMIT = int(os.environ.get("SQL_ROW_LIMIT", "200"))

_READ_ONLY = ("select", "with", "show", "describe", "desc", "explain")


class ReadOnlyError(ValueError):
    """Raised when a statement is not an allowed read-only command."""


class SqlError(RuntimeError):
    """Raised when Zetaris rejects/executes-with-error a statement."""


def _strip(sql: str) -> str:
    """Remove line comments and surrounding whitespace, drop a single trailing ';'."""
    no_comments = "\n".join(
        ln for ln in sql.splitlines() if not ln.strip().startswith("--")
    )
    return no_comments.strip().rstrip(";").strip()


def _guard(sql: str) -> str:
    """Enforce single, read-only statement. Returns the cleaned statement or raises."""
    clean = _strip(sql)
    if not clean:
        raise ReadOnlyError("empty statement")
    if ";" in clean:
        raise ReadOnlyError("only one statement per call (internal ';' found)")
    verb = clean.split(None, 1)[0].lower()
    if verb not in _READ_ONLY:
        raise ReadOnlyError(f"read-only only; '{verb}' is not allowed")
    # inject a LIMIT on bare SELECT/WITH to keep payloads + the source bounded
    if verb in ("select", "with") and not re.search(r"\blimit\b", clean, re.I):
        clean = f"{clean} LIMIT {SQL_ROW_LIMIT}"
    return clean


def _execute(sql: str) -> list:
    response = requests.post(
        ZETARIS_REST_URL.rstrip("/") + "/sql-editor/sqls/run",
        headers={
            "Authorization": "Bearer " + ZETARIS_API_KEY,
            "X-Org-ID": ZETARIS_ORG_ID,
            "X-Request-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
        },
        json={"queryId": str(uuid.uuid4()), "sql": sql, "source": "SqlEditor", "limit": SQL_ROW_LIMIT},
        timeout=60,
    )
    if response.status_code >= 400:
        raise SqlError(f"HTTP {response.status_code}: {response.text[:200]}")
    return response.json().get("data", [])


def run_sql(sql: str) -> list:
    """Run one read-only Lightning SQL statement; return rows. Raises on guard/SQL error."""
    return _execute(_guard(sql))


# --- curated convenience tools (reliable paths the agent can prefer) ---

def search_trials(condition: str | None = None, device_only: bool = False, limit: int = 50) -> list:
    """Trials for a condition. device_only -> join interventions of type DEVICE."""
    lim = min(limit, SQL_ROW_LIMIT)
    if device_only:
        return run_sql(
            "SELECT t.nct_id, t.title, t.status, i.intervention_name "
            "FROM ctgov.trials t JOIN ctgov.interventions i ON t.nct_id = i.nct_id "
            f"WHERE i.intervention_type = 'DEVICE' LIMIT {lim}"
        )
    return run_sql(f"SELECT nct_id, title, status, lead_sponsor FROM ctgov.trials LIMIT {lim}")


def search_devices(term: str, limit: int = 50) -> list:
    """openFDA AI device clearances whose device_name matches `term` (case-insensitive)."""
    safe = term.replace("'", "''")
    lim = min(limit, SQL_ROW_LIMIT)
    return run_sql(
        "SELECT k_number, device_name, applicant, decision_date, specialty "
        f"FROM openfda.ai_devices WHERE lower(device_name) LIKE lower('%{safe}%') LIMIT {lim}"
    )


# --- tool schemas the model sees ---

RUN_SQL_TOOL = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": ("Run ONE read-only Lightning SQL statement (SELECT/SHOW/DESCRIBE) against "
                        "Zetaris and return rows. Tables: ctgov.trials, ctgov.interventions, openfda.ai_devices. "
                        "No trailing semicolon."),
        "parameters": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]},
    },
}
SEARCH_TRIALS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_trials",
        "description": "Find clinical trials; set device_only=true for device-intervention trials.",
        "parameters": {"type": "object", "properties": {
            "condition": {"type": "string"},
            "device_only": {"type": "boolean"}}, "required": []},
    },
}
SEARCH_DEVICES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_devices",
        "description": "Find FDA-cleared AI devices whose name matches a term (e.g. 'transcranial', 'heart rate').",
        "parameters": {"type": "object", "properties": {"term": {"type": "string"}}, "required": ["term"]},
    },
}

TOOLS = [RUN_SQL_TOOL, SEARCH_TRIALS_TOOL, SEARCH_DEVICES_TOOL]
DISPATCH = {"run_sql": run_sql, "search_trials": search_trials, "search_devices": search_devices}
