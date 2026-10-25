"""Evaluation harness — score agent runs against the golden set (evals/cases.py).

  python -m evals.run_evals                 # score the recorded sample (fast, deterministic, CI-safe)
  python -m evals.run_evals --live          # run every case live through the agent, then score
  python -m evals.run_evals --live --only mdd_invariants

Exits non-zero if any check fails, so CI catches grounding regressions."""
import argparse
import os
import sys

from dotenv import load_dotenv

from evals import scorers
from evals.cases import CASES

load_dotenv()


def _score(res, checks, reject_contains=None):
    rows = []
    for name in checks:
        if name == "overclaim_rejected":
            ok, detail = scorers.overclaim_rejected(res, reject_contains or "")
        else:
            fn = scorers.SCORERS.get(name)
            ok, detail = fn(res) if fn else (False, "unknown check")
        rows.append((name, ok, detail))
    return rows


def main():
    ap = argparse.ArgumentParser(description="Score the agent against the grounding golden set.")
    ap.add_argument("--live", action="store_true",
                    help="run cases through the live agent (needs the stack); default scores the recorded sample")
    ap.add_argument("--only", help="run only the case with this id")
    args = ap.parse_args()

    from agent.config import SAMPLE_PATH
    from agent.orchestrator import _load_sample, run

    cases = [c for c in CASES if not args.only or c["id"] == args.only]
    if not cases:
        print(f"no case matching --only {args.only!r}")
        return 2

    if args.live:
        runs = []
        for c in cases:
            print(f"[live] running {c['id']} ...", flush=True)
            res = run(c["question"], stress_claims=c.get("stress_claims") or None, allow_sample=False)
            runs.append((c, res))
    else:
        if not os.path.exists(SAMPLE_PATH):
            print(f"no recorded sample at {SAMPLE_PATH}; run `python -m agent.orchestrator --record` or pass --live")
            return 2
        canonical = next((c for c in cases if c["id"] == "anorexia_cross_source"), None)
        if not canonical:
            print("sample mode scores the canonical case only; pass --live for other cases")
            return 2
        runs = [(canonical, _load_sample())]
        print(f"[sample] scoring recorded run: {SAMPLE_PATH}\n")

    total_ok = total = 0
    failed = []
    for c, res in runs:
        rows = _score(res, c["checks"], c.get("reject_contains"))
        n_ok = sum(1 for _, ok, _ in rows if ok)
        total_ok += n_ok
        total += len(rows)
        print(f"-- {c['id']}  ({n_ok}/{len(rows)})")
        for name, ok, detail in rows:
            print(f"   {'PASS' if ok else 'FAIL'}  {name:<22} {detail}")
        if n_ok < len(rows):
            failed.append(c["id"])
        print()

    print(f"SCORECARD: {total_ok}/{total} checks passed across {len(runs)} case(s)")
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    print("ALL GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
