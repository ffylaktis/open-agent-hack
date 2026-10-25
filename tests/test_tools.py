"""Accept test — tools_zetaris: safety, dict rows, condition filter, curated tools (live)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from agent.tools_zetaris import run_sql, search_trials, search_devices, call_tool, ReadOnlyError, SqlError, _guard

def check(name, fn):
    try:
        fn(); print(f"PASS {name}")
    except AssertionError as e:
        print(f"FAIL {name}: {e}")
    except Exception as e:
        print(f"ERROR {name}: {type(e).__name__}: {str(e)[:160]}")

def t_readonly_blocked():
    for bad in ["DROP LIGHTNING DATABASE CTGOV_REST", "DELETE FROM ctgov.trials",
                "SELECT 1; DROP TABLE x", "SELECT 1 /* ; */ -- hi\nUNION SELECT 2; DROP x"]:
        try:
            _guard(bad); assert False, f"guard allowed: {bad}"
        except ReadOnlyError:
            pass

def t_strip_and_limit():
    g = _guard("SELECT nct_id FROM ctgov.trials;  -- trailing comment")
    assert not g.endswith(";") and "LIMIT" in g.upper(), g

def t_dict_rows():
    rows = run_sql("SELECT COUNT(*) AS n FROM ctgov.trials")
    assert rows and isinstance(rows[0], dict) and str(rows[0]["n"]) == "100", rows

def t_sql_error_raises():
    try:
        run_sql("SELECT * FROM ctgov.nope_not_here"); assert False, "no error raised"
    except SqlError:
        pass

def t_condition_filter():
    yes = search_trials(condition="anorexia", device_only=True, limit=5)
    no = search_trials(condition="zzzznotarealcondition", device_only=True, limit=5)
    assert yes and len(no) == 0, f"filter broken: yes={len(yes)} no={len(no)}"
    assert "intervention_name" in yes[0], yes[0]

def t_neuro_devices():
    rows = search_devices("transcranial", limit=5)
    assert rows and "device_name" in rows[0], f"no neuro devices: {rows}"

def t_call_tool_validation():
    for name, args in [("run_sql", {}), ("search_devices", {}), ("bogus_tool", {"x": 1})]:
        try:
            call_tool(name, args); assert False, f"{name} accepted bad args"
        except ValueError:
            pass

def t_call_tool_returns_sql():
    rows, sql = call_tool("search_trials", {"condition": "anorexia", "device_only": True})
    assert sql and "SELECT" in sql.upper() and isinstance(rows, list), (sql, type(rows))

def t_call_tool_empty_has_sql():
    rows, sql = call_tool("search_devices", {"term": "zzzznotadevice"})
    assert rows == [] and "neuro_devices" in sql, f"empty path lost SQL: {rows} {sql}"

def t_strip_preserves_quoted_dashes():
    g = _guard("SELECT nct_id FROM ctgov.trials t WHERE t.title = 'a--b' LIMIT 1")
    assert "'a--b'" in g, f"quote-safe strip failed: {g}"

for n, f in [("read-only blocked (+comments)", t_readonly_blocked), ("strip+limit", t_strip_and_limit),
             ("dict rows + count", t_dict_rows), ("sql error raises", t_sql_error_raises),
             ("condition filter works", t_condition_filter), ("neuro devices", t_neuro_devices),
             ("call_tool validates args", t_call_tool_validation),
             ("call_tool returns real SQL", t_call_tool_returns_sql),
             ("empty result keeps SQL", t_call_tool_empty_has_sql),
             ("strip preserves quoted --", t_strip_preserves_quoted_dashes)]:
    check(n, f)
