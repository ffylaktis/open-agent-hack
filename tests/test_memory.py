"""H-MEM acceptance tests (offline, deterministic): reject no-source, cross-run recall,
dedupe, and mission scoping."""
import pytest

from agent.memory import Evidence, MemoryStore


def _ev(content="rTMS trialed in anorexia nervosa", sql="SELECT 1"):
    return Evidence(content=content, source="ctgov", provenance={"sql": sql},
                    tags=["rtms", "anorexia"], entities=["rtms"])


def test_reject_no_source():
    with pytest.raises(ValueError):
        Evidence(content="x", source="", provenance={"a": 1})


def test_crossrun_recall_and_ledger(tmp_path):
    path = str(tmp_path / "hmem.json")
    MemoryStore(path=path).write(_ev())              # session A writes
    reloaded = MemoryStore(path=path)                # session B reloads the file
    hits = reloaded.retrieve(query="rtms anorexia", tags=["rtms"])
    assert hits and "rTMS" in hits[0]["content"]
    assert any(e["op"] == "write" for e in reloaded.ledger.entries)


def test_dedupe(tmp_path):
    store = MemoryStore(path=str(tmp_path / "hmem.json"))
    store.write(_ev(sql="SELECT 1"))
    store.write(_ev(sql="SELECT 1"))                 # identical -> deduped
    store.write(_ev(sql="SELECT 2"))                 # different -> new record
    assert len(store.records) == 2


def test_dedupe_returns_stored(tmp_path):
    store = MemoryStore(path=str(tmp_path / "hmem.json"))
    first = store.write(_ev(sql="X"))
    dup = store.write(_ev(sql="X"))                  # duplicate -> returns the STORED record
    assert dup.id == first.id and len(store.records) == 1


def test_mission_scoping(tmp_path):
    path = str(tmp_path / "hmem.json")
    MemoryStore(path=path, mission="runA").write(_ev())
    other = MemoryStore(path=path, mission="runB")   # different mission, same file
    assert other.retrieve(query="rtms anorexia", tags=["rtms"]) == []
    same = MemoryStore(path=path, mission="runA")
    assert same.retrieve(query="rtms anorexia", tags=["rtms"])
