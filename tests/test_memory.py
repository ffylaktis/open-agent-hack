"""Accept test — Step 2: H-MEM write / reject-no-source / cross-run recall / retrieval."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from agent.memory import Evidence, MemoryStore

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_hmem_test.json")

def check(name, fn):
    try:
        fn(); print(f"PASS {name}")
    except AssertionError as e:
        print(f"FAIL {name}: {e}")
    except Exception as e:
        print(f"ERROR {name}: {type(e).__name__}: {str(e)[:160]}")

def t_reject_no_source():
    try:
        Evidence(content="x", source="", provenance={"a": 1}); assert False, "accepted empty source"
    except ValueError:
        pass

def t_write_and_crossrun_recall():
    if os.path.exists(TMP):
        os.remove(TMP)
    a = MemoryStore(path=TMP)                      # session A
    a.write(Evidence(content="rTMS trialed in anorexia nervosa",
                     source="ctgov", provenance={"sql": "SELECT ..."},
                     tags=["rtms", "anorexia"], entities=["rtms"]))
    b = MemoryStore(path=TMP)                       # session B: fresh instance reloads file
    hits = b.retrieve(query="rtms anorexia", tags=["rtms"])
    assert hits and "rTMS" in hits[0]["content"], f"cross-run recall failed: {hits}"
    assert b.ledger.entries and b.ledger.entries[0]["op"] == "write", "trust ledger not persisted"
    os.remove(TMP)

for n, f in [("reject no-source", t_reject_no_source), ("write + cross-run recall + ledger", t_write_and_crossrun_recall)]:
    check(n, f)
