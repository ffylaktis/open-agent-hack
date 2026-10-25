"""Orchestrator — the agent loop:
   plan -> gather evidence (Analyst per sub-q, cross_source for 'cross') -> draft cited claims
   -> Evaluator verifies each (unsupported dropped) -> assemble a cited answer + a trace.
Run:  python -m agent.orchestrator "your question"
"""
import sys
import uuid
from dotenv import load_dotenv
load_dotenv()

from agent import planner, analyst, reporter, evaluator          # noqa: E402
from agent.cross_source import cross_source                      # noqa: E402
from agent.memory import MemoryStore                             # noqa: E402
from agent.trace import Trace                                    # noqa: E402


def _cite(by_id, i):
    r = by_id.get(i)
    if not r:
        return i
    sql = (r.get("provenance") or {}).get("sql") or ""
    return f"{r['source']}[{sql[:48]}]"


def _assemble(question, supported, dropped, by_id):
    lines = [f"Q: {question}", ""]
    if supported:
        lines.append("ANSWER (every claim evidence-backed):")
        for v in supported:
            cites = "; ".join(_cite(by_id, i) for i in v["evidence_ids"]) or "—"
            lines.append(f"  • {v['claim']}\n      ↳ evidence: {cites}")
    else:
        lines.append("No claim passed evidence verification.")
    if dropped:
        lines.append("")
        lines.append("REJECTED by the Evaluator (not supported by evidence):")
        for v in dropped:
            lines.append(f"  ✗ {v['claim']}\n      ↳ {v['reason']}")
    return "\n".join(lines)


def run(question, mission=None, stress_claims=None):
    mission = mission or ("run_" + uuid.uuid4().hex[:8])
    store = MemoryStore(mission=mission)                          # scoped per run — no contamination
    trace = Trace()

    p = planner.plan(question, trace)
    condition, subs = p["condition"], p["subquestions"]

    for s in subs:
        if s["source"] == "cross":
            cross_source(condition, store, trace)
        else:
            analyze_q = dict(s)
            analyst.analyze(analyze_q, store, trace)

    evidence = store.all()
    by_id = {r["id"]: r for r in evidence}
    claims = reporter.report(question, evidence, trace)

    # stress claims (demo): candidate assertions evaluated against ALL evidence
    for sc in (stress_claims or []):
        claims.append({"text": sc, "evidence_ids": list(by_id.keys())})

    verdicts = [evaluator.evaluate(c, by_id, trace) for c in claims]
    supported = [v for v in verdicts if v["supported"]]
    dropped = [v for v in verdicts if not v["supported"]]

    return {"question": question, "mission": mission, "condition": condition,
            "answer": _assemble(question, supported, dropped, by_id),
            "supported": supported, "dropped": dropped, "evidence": evidence, "trace": trace}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What neuromodulation is being trialed for anorexia nervosa, and is any of it FDA-cleared for that use?"
    res = run(q, stress_claims=["rTMS is FDA-cleared to treat anorexia nervosa."])
    print("\n".join(res["trace"].summary()))
    print("\n" + "=" * 70 + "\n" + res["answer"])
