"""Orchestrator — the agent loop:
   plan -> gather evidence (Analyst per sub-q, cross_source for 'cross') -> draft cited claims
   -> Evaluator verifies each -> on rejections, re-report with feedback (<= MAX_ROUNDS)
   -> assemble a cited answer + trace + telemetry.
Run:   python -m agent.orchestrator "your question"
Record a demo sample:  python -m agent.orchestrator --record "..."
Replay (bulletproof demo): set SAMPLE_MODE=1 in .env
"""
import json
import os
import sys
import time
import uuid
from dotenv import load_dotenv
load_dotenv()

from agent import planner, analyst, reporter, evaluator                         # noqa: E402
from agent.cross_source import cross_source                                     # noqa: E402
from agent.memory import MemoryStore                                            # noqa: E402
from agent.trace import Trace                                                   # noqa: E402
from agent.config import MAX_ROUNDS, RUN_BUDGET_SECONDS, SAMPLE_MODE, SAMPLE_PATH  # noqa: E402


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
        lines.append("\nREJECTED by the Evaluator (not supported by evidence):")
        for v in dropped:
            lines.append(f"  ✗ {v['claim']}\n      ↳ {v['reason']}")
    return "\n".join(lines)


def _telemetry(trace):
    routes, tokens, receipts = {}, 0, []
    for e in trace.events:
        if e.get("route"):
            routes[e["route"]] = routes.get(e["route"], 0) + 1
        tokens += e.get("tokens") or 0
        if e.get("receipt_id"):
            receipts.append(e["receipt_id"])
    return {"routes": routes, "total_tokens": tokens, "receipts": receipts[:5]}


def save_sample(res, path=SAMPLE_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {"question": res["question"], "condition": res["condition"], "answer": res["answer"],
            "supported": res["supported"], "dropped": res["dropped"], "telemetry": res["telemetry"],
            "evidence": [{k: r.get(k) for k in ("id", "source", "content")} for r in res["evidence"]],
            "trace": res["trace"].events}
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2, default=str)
    return path


def _load_sample(path=SAMPLE_PATH):
    d = json.load(open(path, encoding="utf-8"))
    t = Trace(); t.events = d.get("trace", [])
    d["trace"] = t
    d["replayed"] = True
    return d


def run(question, mission=None, stress_claims=None):
    if SAMPLE_MODE and os.path.exists(SAMPLE_PATH):          # bulletproof demo replay
        return _load_sample()

    mission = mission or ("run_" + uuid.uuid4().hex[:8])
    store = MemoryStore(path=None, mission=mission)          # ephemeral per-run store (no disk growth/contamination)
    trace = Trace()
    t0 = time.monotonic()

    p = planner.plan(question, trace)
    condition, subs = p["condition"], p["subquestions"]

    for s in subs:
        if time.monotonic() - t0 > RUN_BUDGET_SECONDS:
            trace.add("orchestrator", "budget_stop", {"phase": "gather", "elapsed": round(time.monotonic() - t0)})
            break
        if s["source"] == "cross":
            cross_source(condition, store, trace)
        else:
            analyst.analyze(dict(s), store, trace)

    evidence = store.all()
    by_id = {r["id"]: r for r in evidence}

    supported, all_dropped, feedback = {}, {}, None
    for rnd in range(MAX_ROUNDS):
        claims = reporter.report(question, evidence, trace, feedback=feedback)
        verdicts = []
        for c in claims:
            if time.monotonic() - t0 > RUN_BUDGET_SECONDS:   # budget guards evaluate too, not just gather
                trace.add("orchestrator", "budget_stop", {"phase": "evaluate", "elapsed": round(time.monotonic() - t0)})
                break
            verdicts.append(evaluator.evaluate(c, by_id, trace))
        for v in verdicts:
            if v["supported"]:
                supported[v["claim"]] = v
                all_dropped.pop(v["claim"], None)            # recovered -> no longer rejected
            else:
                all_dropped[v["claim"]] = v                  # track ALL rejections, not just the last round
        round_dropped = [v for v in verdicts if not v["supported"]]
        trace.add("orchestrator", "round", {"round": rnd, "supported": len(supported), "dropped": len(round_dropped)})
        if not round_dropped or time.monotonic() - t0 > RUN_BUDGET_SECONDS:
            break
        feedback = round_dropped                             # revise unsupported claims next round

    for sc in (stress_claims or []):                         # demo: candidate assertions vs ALL evidence
        v = evaluator.evaluate({"text": sc, "evidence_ids": list(by_id)}, by_id, trace)
        if v["supported"]:
            supported[v["claim"]] = v
        else:
            all_dropped[v["claim"]] = v

    sup = list(supported.values())
    dropped = [v for k, v in all_dropped.items() if k not in supported]
    res = {"question": question, "mission": mission, "condition": condition,
           "answer": _assemble(question, sup, dropped, by_id),
           "supported": sup, "dropped": dropped, "evidence": evidence,
           "trace": trace, "telemetry": _telemetry(trace)}
    return res


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if a != "--record"]
    record = "--record" in sys.argv
    q = " ".join(argv) or ("What neuromodulation is being trialed for anorexia nervosa, "
                           "and is any of it FDA-cleared for that use?")
    res = run(q, stress_claims=["rTMS is FDA-cleared to treat anorexia nervosa."])
    print("\n".join(res["trace"].summary()))
    print("\n" + "=" * 70 + "\n" + res["answer"])
    print("\n" + "-" * 70 + f"\ntelemetry: {res['telemetry']}")
    if record:
        print("saved sample ->", save_sample(res))
