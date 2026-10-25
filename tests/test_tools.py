"""Accept test — Step 1: tools_zetaris safety + curated tools (hits live Zetaris)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from agent.tools_zetaris import run_sql, search_trials, search_devices, ReadOnlyError, _guard

def check(name, fn):
    try:
        fn(); print(f"PASS {name}")
    except AssertionError as e:
        print(f"FAIL {name}: {e}")
    except Exception as e:
        print(f"ERROR {name}: {type(e).__name__}: {str(e)[:160]}")

def t_readonly_blocked():
    for bad in ["DROP LIGHTNING DATABASE CTGOV_REST", "DELETE FROM ctgov.trials", "SELECT 1; DROP TABLE x"]:
        try:
            _guard(bad); assert False, f"guard allowed: {bad}"
        except ReadOnlyError:
            pass

def t_strip_and_limit():
    g = _guard("SELECT nct_id FROM ctgov.trials;")
    assert not g.endswith(";"), "trailing ; not stripped"
    assert "LIMIT" in g.upper(), "LIMIT not injected"

def t_select_runs():
    rows = run_sql("SELECT COUNT(*) FROM ctgov.trials;")
    assert rows and str(rows[0][0]) == "100", f"unexpected count: {rows}"

def t_search_trials_device():
    rows = search_trials(device_only=True, limit=5)
    assert rows and len(rows) <= 5, f"no device trials: {rows}"

def t_search_devices():
    rows = search_devices("transcranial", limit=5)
    assert isinstance(rows, list), "search_devices did not return a list"

for n, f in [("read-only blocked", t_readonly_blocked), ("strip+limit", t_strip_and_limit),
             ("SELECT runs", t_select_runs), ("search_trials device", t_search_trials_device),
             ("search_devices", t_search_devices)]:
    check(n, f)
