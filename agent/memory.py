"""H-MEM — the Meterless Engine (focused Python port): canonical evidence record +
tiered store + retrieval + trust ledger. Per the H-MEM spec, `source` is mandatory —
a record with no source is rejected by construction. (reference/meterless-hmem/AGENTS.md)
"""
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from agent.config import HMEM_PATH


@dataclass
class Evidence:
    content: str
    source: str                      # mandatory ("ctgov" | "openfda")
    provenance: dict                 # mandatory for new writes: {tool, args, sql}
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


class TrustLedger:
    """Append-only audit of every mutation."""
    def __init__(self, entries=None):
        self.entries = entries or []

    def record(self, op, ev_id, note=""):
        self.entries.append({"op": op, "id": ev_id, "at": round(time.time(), 3), "note": note})


class MemoryStore:
    """Tiered persistent store (working layer). JSON-backed so recall survives across runs."""
    def __init__(self, path=HMEM_PATH):
        self.path = path
        self.records = {}
        self.ledger = TrustLedger()
        self._load()

    def _load(self):
        if self.path and os.path.exists(self.path):
            try:
                data = json.load(open(self.path, encoding="utf-8"))
                self.records = {r["id"]: r for r in data.get("records", [])}
                self.ledger = TrustLedger(data.get("ledger", []))
            except Exception:
                pass

    def _persist(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        json.dump({"records": list(self.records.values()), "ledger": self.ledger.entries},
                  open(self.path, "w", encoding="utf-8"), indent=2, default=str)

    def write(self, ev: Evidence) -> Evidence:
        self.records[ev.id] = asdict(ev)
        self.ledger.record("write", ev.id, note=ev.source)
        self._persist()
        return ev

    def all(self):
        return list(self.records.values())

    def retrieve(self, query="", tags=None, limit=10):
        """Keyword + tag/entity ranking (no embeddings — the evidence set is small)."""
        want = set(t.lower() for t in (tags or []))
        words = [w for w in query.lower().split() if len(w) > 3]
        scored = []
        for r in self.records.values():
            have = set(t.lower() for t in r.get("tags", [])) | set(e.lower() for e in r.get("entities", []))
            score = 2 * len(want & have)
            content = r.get("content", "").lower()
            score += sum(1 for w in words if w in content)
            score += r.get("confidence", 0)
            if score > 0:
                scored.append((score, r))
        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:limit]]
