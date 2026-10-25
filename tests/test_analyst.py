"""Analyst acceptance test (live): a sub-question becomes well-formed, self-describing Evidence.

NB: by design the Analyst *may* answer without querying (see review finding #2), so we don't
hard-require non-empty output here — the eval harness measures end-to-end grounding instead.
What we require: the call runs against the live stack and any Evidence it writes is well-formed."""
import pytest

from agent.analyst import analyze
from agent.memory import MemoryStore
from agent.trace import Trace


@pytest.mark.live
def test_analyst_evidence_is_wellformed(tmp_path):
    store = MemoryStore(path=str(tmp_path / "hmem.json"))
    subq = {"question": "Which device interventions have been trialed for anorexia nervosa?",
            "source": "ctgov"}
    evidence = analyze(subq, store, Trace())
    assert isinstance(evidence, list)
    for e in evidence:
        assert e.source in ("ctgov", "openfda")
        assert e.provenance
        assert not e.rows or isinstance(e.rows[0], dict)
