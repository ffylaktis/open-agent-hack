"""End-to-end acceptance test (live): the full agent produces a cited answer, reconciles both
sources, runs on the Meterless route, and the Evaluator rejects the FDA-cleared overclaim."""
import pytest

from agent.orchestrator import run

Q = "What neuromodulation is being trialed for anorexia nervosa, and is any of it FDA-cleared for that use?"
OVERCLAIM = "rTMS is FDA-cleared to treat anorexia nervosa."


@pytest.mark.live
def test_e2e_cited_answer_and_overclaim_rejected():
    res = run(Q, stress_claims=[OVERCLAIM])
    dropped = [d["claim"] for d in res["dropped"]]
    sources = {e["source"] for e in res["evidence"]}
    telemetry = res.get("telemetry", {})

    assert res["answer"]
    assert any(OVERCLAIM[:20] in claim for claim in dropped), "overclaim not rejected"
    assert "ctgov" in sources and "openfda" in sources, "cross-source evidence missing"
    assert all(v["evidence_ids"] or not v["supported"] for v in res["supported"]), "supported claim uncited"
    assert telemetry.get("total_tokens", 0) > 0
    assert "meterless" in telemetry.get("routes", {}), "did not run on the Meterless route"
