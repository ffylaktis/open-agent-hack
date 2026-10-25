"""Accept test — H-MEM: reject no-source, cross-run recall, dedupe, atomic persist."""
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

def _ev(content="rTMS trialed in anorexia nervosa", sql="SELECT 1"):
    return Evidence(content=content, source="ctgov", provenance={"sql": sql},
                    tags=["rtms", "anorexia"], entities=["rtms"])

def t_reject_no_source():
    try:
        Evidence(content="x", source="", provenance={"a": 1}); assert False, "accepted empty source"
    except ValueError:
        pass

def t_crossrun_recall_and_ledger():
    if os.path.exists(TMP):
        os.remove(TMP)
    MemoryStore(path=TMP).write(_ev())              # session A
    b = MemoryStore(path=TMP)                        # session B reloads file
    hits = b.retrieve(query="rtms anorexia", tags=["rtms"])
    assert hits and "rTMS" in hits[0]["content"], f"recall failed: {hits}"
    assert any(e["op"] == "write" for e in b.ledger.entries), "ledger not persisted"
    os.remove(TMP)

def t_dedupe():
    if os.path.exists(TMP):
        os.remove(TMP)
    s = MemoryStore(path=TMP)
    s.write(_ev(sql="SELECT 1"))
    s.write(_ev(sql="SELECT 1"))                     # identical -> deduped
    s.write(_ev(sql="SELECT 2"))                     # different -> new
    assert len(s.records) == 2, f"dedupe failed: {len(s.records)} records"
    os.remove(TMP)

def t_mission_scoping():
    if os.path.exists(TMP):
        os.remove(TMP)
    MemoryStore(path=TMP, mission="runA").write(_ev())        # evidence under mission A
    other = MemoryStore(path=TMP, mission="runB")             # different mission, same file
    assert other.retrieve(query="rtms anorexia", tags=["rtms"]) == [], "mission leak: runB saw runA"
    same = MemoryStore(path=TMP, mission="runA")
    assert same.retrieve(query="rtms anorexia", tags=["rtms"]), "runA could not recall its own evidence"
    os.remove(TMP)

for n, f in [("reject no-source", t_reject_no_source),
             ("cross-run recall + ledger", t_crossrun_recall_and_ledger),
             ("dedupe by (source,sql)", t_dedupe),
             ("mission scoping (no leak)", t_mission_scoping)]:
    check(n, f)
