"""tools_zetaris acceptance tests.

Offline: the read-only guard, strip/limit, and argument validation (no network).
Live (needs Zetaris): dict rows, SQL errors, condition filter, curated tools."""
import pytest

from agent.config import SQL_ROW_LIMIT
from agent.tools_zetaris import (ReadOnlyError, SqlError, _guard, call_tool,
                                 run_sql, search_devices, search_trials)


# ---- offline: safety + validation (no network) ----
@pytest.mark.parametrize("bad", [
    "DROP LIGHTNING DATABASE CTGOV_REST",
    "DELETE FROM ctgov.trials",
    "SELECT 1; DROP TABLE x",
    "SELECT 1 /* ; */ -- hi\nUNION SELECT 2; DROP x",
])
def test_readonly_blocked(bad):
    with pytest.raises(ReadOnlyError):
        _guard(bad)


def test_strip_and_limit():
    g = _guard("SELECT nct_id FROM ctgov.trials;  -- trailing comment")
    assert not g.endswith(";") and "LIMIT" in g.upper()


def test_strip_preserves_quoted_dashes():
    g = _guard("SELECT nct_id FROM ctgov.trials t WHERE t.title = 'a--b' LIMIT 1")
    assert "'a--b'" in g


def test_limit_injected_when_literal_contains_limit():
    # regression (review finding #4): 'limit' inside a literal must not suppress the injected LIMIT
    g = _guard("SELECT device_name FROM openfda.neuro_devices WHERE device_name LIKE '%limit%'")
    assert g.endswith(f"LIMIT {SQL_ROW_LIMIT}"), g


@pytest.mark.parametrize("name,args", [("run_sql", {}), ("search_devices", {}), ("bogus_tool", {"x": 1})])
def test_call_tool_validation(name, args):
    with pytest.raises(ValueError):
        call_tool(name, args)


# ---- live: real Zetaris ----
@pytest.mark.live
def test_dict_rows():
    rows = run_sql("SELECT COUNT(*) AS n FROM ctgov.trials")
    assert rows and isinstance(rows[0], dict) and int(rows[0]["n"]) >= 1


@pytest.mark.live
def test_sql_error_raises():
    with pytest.raises(SqlError):
        run_sql("SELECT * FROM ctgov.nope_not_here")


@pytest.mark.live
def test_condition_filter():
    yes = search_trials(condition="anorexia", device_only=True, limit=5)
    no = search_trials(condition="zzzznotarealcondition", device_only=True, limit=5)
    assert yes and len(no) == 0 and "intervention_name" in yes[0]


@pytest.mark.live
def test_neuro_devices():
    rows = search_devices("transcranial", limit=5)
    assert rows and "device_name" in rows[0]


@pytest.mark.live
def test_call_tool_returns_real_sql():
    rows, sql = call_tool("search_trials", {"condition": "anorexia", "device_only": True})
    assert sql and "SELECT" in sql.upper() and isinstance(rows, list)


@pytest.mark.live
def test_call_tool_empty_keeps_sql():
    rows, sql = call_tool("search_devices", {"term": "zzzznotadevice"})
    assert rows == [] and "neuro_devices" in sql
