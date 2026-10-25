"""Data-layer tools: safe, read-only access to Zetaris over REST.

Enforced (Zetaris AGENTS.md + PRD safety): one statement/call, no trailing ';',
read-only verbs only, LIMIT injected on bare SELECT/WITH, qualified names.
Rows are returned as dicts (column name -> value) using the response `headers`,
so evidence is self-describing. Query errors (HTTP 400 + {"msg": ...}) raise SqlError.
"""
import json
import os
import re
import uuid
import requests

ZETARIS_REST_URL = os.environ.get("ZETARIS_REST_URL", "http://localhost:8888/api/v1.0")
ZETARIS_ORG_ID = os.environ.get("ZETARIS_ORG_ID", "1")
ZETARIS_API_KEY = os.environ.get("ZETARIS_API_KEY", "")
SQL_ROW_LIMIT = int(os.environ.get("SQL_ROW_LIMIT", "200"))

_READ_ONLY = ("select", "with", "show", "describe", "desc", "explain")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


class ReadOnlyError(ValueError):
    """Statement is not an allowed read-only command."""


class SqlError(RuntimeError):
    """Zetaris rejected/failed the statement."""


def _strip(sql: str) -> str:
    """Remove block + line comments, trim, drop a single trailing ';'."""
    s = _BLOCK_COMMENT.sub(" ", sql)
    s = "\n".join(ln.split("--", 1)[0] for ln in s.splitlines())
    return s.strip().rstrip(";").strip()


def _guard(sql: str) -> str:
    clean = _strip(sql)
    if not clean:
        raise ReadOnlyError("empty statement")
    if ";" in clean:
        raise ReadOnlyError("only one statement per call (internal ';' found)")
    verb = clean.split(None, 1)[0].lower()
    if verb not in _READ_ONLY:
        raise ReadOnlyError(f"read-only only; '{verb}' is not allowed")
    if verb in ("select", "with") and not re.search(r"\blimit\b", clean, re.I):
        clean = f"{clean} LIMIT {SQL_ROW_LIMIT}"
    return clean


def _execute(sql: str) -> list:
    resp = requests.post(
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
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("msg") or resp.text
        except Exception:
            msg = resp.text
        raise SqlError(f"HTTP {resp.status_code}: {str(msg)[:300]}")
    body = resp.json()
    headers = body.get("headers") or []
    data = body.get("data") or []                 # DDL responses may carry no data — that's fine
    if headers:
        return [dict(zip(headers, row)) for row in data]
    return [{f"c{i}": v for i, v in enumerate(row)} for row in data]


def run_sql(sql: str) -> list:
    """Run one read-only Lightning SQL statement; return list[dict]. Raises on guard/SQL error."""
    return _execute(_guard(sql))


def execute_admin(sql: str) -> list:
    """Privileged path for data registration (DDL). Bypasses the read-only guard —
    NOT for agent use; only the trusted data-setup scripts call this."""
    return _execute(_strip(sql))


# --- curated convenience tools ---

def search_trials(condition: str | None = None, device_only: bool = False, limit: int = 50) -> list:
    """Trials, optionally filtered to a condition and/or device interventions."""
    lim = min(limit, SQL_ROW_LIMIT)
    cond_sql = ""
    if condition:
        c = condition.replace("'", "''")
        cond_sql = f"(lower(concat_ws(' ', t.conditions)) LIKE lower('%{c}%') OR lower(t.title) LIKE lower('%{c}%'))"
    if device_only:
        q = ("SELECT t.nct_id, t.title, t.status, i.intervention_name, i.intervention_type "
             "FROM ctgov.trials t JOIN ctgov.interventions i ON t.nct_id = i.nct_id "
             "WHERE i.intervention_type = 'DEVICE'")
        if cond_sql:
            q += " AND " + cond_sql
        return run_sql(q + f" LIMIT {lim}")
    q = "SELECT nct_id, title, status, lead_sponsor FROM ctgov.trials t"
    if cond_sql:
        q += " WHERE " + cond_sql
    return run_sql(q + f" LIMIT {lim}")


def search_devices(term: str, limit: int = 50) -> list:
    """FDA-cleared neuromodulation devices (openfda.neuro_devices) whose name matches `term`."""
    safe = term.replace("'", "''")
    lim = min(limit, SQL_ROW_LIMIT)
    return run_sql(
        "SELECT k_number, device_name, applicant, decision_date, specialty "
        f"FROM openfda.neuro_devices WHERE lower(device_name) LIKE lower('%{safe}%') LIMIT {lim}"
    )


# --- tool schemas the model sees ---

RUN_SQL_TOOL = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": ("Run ONE read-only Lightning SQL statement (SELECT/SHOW/DESCRIBE) and return rows. "
                        "Tables: ctgov.trials, ctgov.interventions, openfda.neuro_devices (cleared TMS/neuromod), "
                        "openfda.ai_devices (cleared AI devices). No trailing semicolon; qualify names."),
        "parameters": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]},
    },
}
SEARCH_TRIALS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_trials",
        "description": "Find trials; pass condition to filter, device_only=true for device-intervention trials.",
        "parameters": {"type": "object", "properties": {
            "condition": {"type": "string"}, "device_only": {"type": "boolean"}}, "required": []},
    },
}
SEARCH_DEVICES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_devices",
        "description": "Find FDA-cleared neuromodulation devices by name term (e.g. 'transcranial').",
        "parameters": {"type": "object", "properties": {"term": {"type": "string"}}, "required": ["term"]},
    },
}

TOOLS = [RUN_SQL_TOOL, SEARCH_TRIALS_TOOL, SEARCH_DEVICES_TOOL]
DISPATCH = {"run_sql": run_sql, "search_trials": search_trials, "search_devices": search_devices}
