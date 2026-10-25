"""Data-layer tools: safe, read-only access to Zetaris over REST.

Enforced (Zetaris AGENTS.md + PRD safety): one statement/call, no trailing ';',
read-only verbs only, LIMIT injected on bare SELECT/WITH, qualified names.
Rows are returned as dicts (column name -> value) using the response `headers`,
so evidence is self-describing. Query errors (HTTP 400 + {"msg": ...}) raise SqlError.
"""
import os
import re
import uuid
import requests
from agent.config import SQL_ROW_LIMIT

ZETARIS_REST_URL = os.environ.get("ZETARIS_REST_URL", "http://localhost:8888/api/v1.0")
ZETARIS_ORG_ID = os.environ.get("ZETARIS_ORG_ID", "1")
ZETARIS_API_KEY = os.environ.get("ZETARIS_API_KEY", "")

_READ_ONLY = ("select", "with", "show", "describe", "desc", "explain")


class ReadOnlyError(ValueError):
    """Statement is not an allowed read-only command."""


class SqlError(RuntimeError):
    """Zetaris rejected/failed the statement."""


def _strip(sql: str) -> str:
    """Remove `--` line and `/* */` block comments, trim, drop a trailing ';'.
    Quote-aware: `--`/`/*` inside a single-quoted string literal are preserved."""
    out, i, n, in_str = [], 0, len(sql), False
    while i < n:
        ch = sql[i]
        if in_str:
            out.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":   # escaped '' inside a literal
                    out.append("'")
                    i += 2
                    continue
                in_str = False
            i += 1
        elif ch == "'":
            in_str = True
            out.append(ch)
            i += 1
        elif ch == "-" and i + 1 < n and sql[i + 1] == "-":        # line comment
            while i < n and sql[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < n and sql[i + 1] == "*":        # block comment
            i += 2
            while i + 1 < n and not (sql[i] == "*" and sql[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out).strip().rstrip(";").strip()


def _without_literals(sql: str) -> str:
    """Return sql with the CONTENTS of single-quoted literals removed, so keyword checks (e.g.
    LIMIT) can't match text inside a literal like '%limit%'. Quote-aware ('' escape)."""
    out, i, n, in_str = [], 0, len(sql), False
    while i < n:
        ch = sql[i]
        if in_str:
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":   # escaped '' inside a literal
                    i += 2
                    continue
                in_str = False
                out.append("'")
            i += 1
        elif ch == "'":
            in_str = True
            out.append("'")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _guard(sql: str) -> str:
    clean = _strip(sql)
    if not clean:
        raise ReadOnlyError("empty statement")
    if ";" in clean:
        raise ReadOnlyError("only one statement per call (internal ';' found)")
    verb = clean.split(None, 1)[0].lower()
    if verb not in _READ_ONLY:
        raise ReadOnlyError(f"read-only only; '{verb}' is not allowed")
    if verb in ("select", "with") and not re.search(r"\blimit\b", _without_literals(clean), re.I):
        clean = f"{clean} LIMIT {SQL_ROW_LIMIT}"
    return clean


def _execute(sql: str) -> list:
    try:
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
    except requests.RequestException as e:                 # network/timeout -> uniform SqlError
        raise SqlError(f"Zetaris request failed: {str(e)[:200]}") from e
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
        return [dict(zip(headers, row, strict=False)) for row in data]
    return [{f"c{i}": v for i, v in enumerate(row)} for row in data]


def run_sql(sql: str) -> list:
    """Run one read-only Lightning SQL statement; return list[dict]. Raises on guard/SQL error."""
    return _execute(_guard(sql))


def execute_admin(sql: str) -> list:
    """Privileged path for data registration (DDL). Bypasses the read-only guard —
    NOT for agent use; only the trusted data-setup scripts call this."""
    return _execute(_strip(sql))


# --- curated convenience tools (SQL built in one place so provenance always has it) ---

def _trials_sql(condition=None, device_only=False, limit=50):
    lim = min(int(limit or 50), SQL_ROW_LIMIT)
    cond = ""
    if condition:
        c = str(condition).replace("'", "''")
        cond = f"(lower(concat_ws(' ', t.conditions)) LIKE lower('%{c}%') OR lower(t.title) LIKE lower('%{c}%'))"
    if device_only:
        q = ("SELECT t.nct_id, t.title, t.status, i.intervention_name, i.intervention_type "
             "FROM ctgov.trials t JOIN ctgov.interventions i ON t.nct_id = i.nct_id "
             "WHERE i.intervention_type = 'DEVICE'")
        if cond:
            q += " AND " + cond
        return q + f" LIMIT {lim}"
    q = "SELECT nct_id, title, status, lead_sponsor FROM ctgov.trials t"
    if cond:
        q += " WHERE " + cond
    return q + f" LIMIT {lim}"


def _devices_sql(term, limit=50):
    safe = str(term).replace("'", "''")
    lim = min(int(limit or 50), SQL_ROW_LIMIT)
    return ("SELECT k_number, device_name, applicant, decision_date, specialty "
            f"FROM openfda.neuro_devices WHERE lower(device_name) LIKE lower('%{safe}%') LIMIT {lim}")


def search_trials(condition=None, device_only=False, limit=50) -> list:
    """Trials, optionally filtered to a condition and/or device interventions."""
    return run_sql(_trials_sql(condition, device_only, limit))


def search_devices(term, limit=50) -> list:
    """FDA-cleared neuromodulation devices (openfda.neuro_devices) whose name matches `term`."""
    return run_sql(_devices_sql(term, limit))


def call_tool(name: str, args: dict):
    """Dispatch a model tool-call. Returns (rows, sql). Validates required args;
    raises ValueError on missing/unknown so the agent can recover instead of crashing."""
    if name == "run_sql":
        sql = args.get("sql")
        if not sql:
            raise ValueError("run_sql requires a 'sql' argument")
        guarded = _guard(sql)
        return _execute(guarded), guarded
    if name == "search_trials":
        sql = _trials_sql(args.get("condition"), bool(args.get("device_only")), args.get("limit", 50))
        return _execute(_guard(sql)), sql
    if name == "search_devices":
        if not args.get("term"):
            raise ValueError("search_devices requires a 'term' argument")
        sql = _devices_sql(args["term"], args.get("limit", 50))
        return _execute(_guard(sql)), sql
    raise ValueError(f"unknown tool '{name}'")


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
