"""H-MEM — the Meterless Engine (focused Python port): canonical evidence record +
tiered store + retrieval + trust ledger. `source` + `provenance` are mandatory
(spec: a record with no source is rejected by construction). Writes are atomic and
de-duplicated. (reference/meterless-hmem/AGENTS.md)
"""
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from agent.config import HMEM_PATH


@dataclass
class Evidence:
    content: str
    source: str                      # mandatory ("ctgov" | "openfda")
    provenance: dict                 # mandatory: {tool, args, sql}
    confidence: float = 1.0
    type: str = "factual"
    layer: str = "working"
    tags: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    id: str = field(default_factory=lambda: "ev_" + uuid.uuid4().hex[:10])
    created_at: float = field(default_factory=lambda: round(time.time(), 3))

    def __post_init__(self):
        if not self.source:
            raise ValueError("H-MEM: every memory requires a `source` — rejected by construction")
        if not self.provenance:
            raise ValueError("H-MEM: new writes require `provenance`")

    def dedupe_key(self):
        p = self.provenance or {}
        detail = p.get("sql") or json.dumps(p.get("args", {}), sort_keys=True, default=str)
        return f"{self.source}|{detail}"


class TrustLedger:
    def __init__(self, entries=None):
        self.entries = entries or []

    def record(self, op, ev_id, note=""):
        self.entries.append({"op": op, "id": ev_id, "at": round(time.time(), 3), "note": note})


class MemoryStore:
    """Tiered persistent store (working layer), JSON-backed, atomic writes, de-duplicated."""
    def __init__(self, path=HMEM_PATH):
        self.path = path
        self.records = {}
        self.ledger = TrustLedger()
        self._keys = {}            # dedupe_key -> id
        self._load()

    def _load(self):
        if self.path and os.path.exists(self.path):
            try:
                data = json.load(open(self.path, encoding="utf-8"))
                self.records = {r["id"]: r for r in data.get("records", [])}
                self.ledger = TrustLedger(data.get("ledger", []))
                self._keys = {r.get("_key"): r["id"] for r in self.records.values() if r.get("_key")}
            except Exception as e:                 # do not silently lose memory
                print(f"[H-MEM] WARNING: could not load {self.path}: {e}", file=sys.stderr)

    def _persist(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"records": list(self.records.values()), "ledger": self.ledger.entries},
                      f, indent=2, default=str)
        os.replace(tmp, self.path)                 # atomic

    def write(self, ev: Evidence) -> Evidence:
        key = ev.dedupe_key()
        if key in self._keys:                      # de-dupe: return the existing record's view
            existing = self.records[self._keys[key]]
            self.ledger.record("dedupe", existing["id"], note=key)
            return ev
        rec = asdict(ev)
        rec["_key"] = key
        self.records[ev.id] = rec
        self._keys[key] = ev.id
        self.ledger.record("write", ev.id, note=ev.source)
        self._persist()
        return ev

    def all(self):
        return list(self.records.values())

    def retrieve(self, query="", tags=None, limit=10):
        """Rank by tag/entity + keyword match; confidence only breaks ties. No embeddings."""
        want = set(t.lower() for t in (tags or []))
        words = [w for w in query.lower().split() if len(w) > 3]
        scored = []
        for r in self.records.values():
            have = set(t.lower() for t in r.get("tags", [])) | set(e.lower() for e in r.get("entities", []))
            match = 2 * len(want & have) + sum(1 for w in words if w in r.get("content", "").lower())
            if match > 0:                           # require a real match to surface
                scored.append((match + 0.1 * r.get("confidence", 0), r))
        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:limit]]
