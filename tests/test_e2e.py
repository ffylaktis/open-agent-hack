"""Accept test — full pipeline: cited answer, cross-source evidence, Evaluator rejects the overclaim."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from agent.orchestrator import run

Q = "What neuromodulation is being trialed for anorexia nervosa, and is any of it FDA-cleared for that use?"
OVERCLAIM = "rTMS is FDA-cleared to treat anorexia nervosa."

res = run(Q, stress_claims=[OVERCLAIM])
dropped = [d["claim"] for d in res["dropped"]]
srcs = {e["source"] for e in res["evidence"]}

ok = True
def req(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg); ok = ok and cond

req(bool(res["answer"]), "produced an answer")
req(any(OVERCLAIM[:20] in t for t in dropped), "Evaluator rejected the FDA-cleared overclaim")
req("ctgov" in srcs and "openfda" in srcs, "cross-source evidence present (ctgov + openfda)")
req(all(v["evidence_ids"] or not v["supported"] for v in res["supported"]), "every supported claim is cited")
print(f"  supported={len(res['supported'])} dropped={len(res['dropped'])} evidence={len(res['evidence'])} route=meterless")
print("E2E OK" if ok else "E2E FAILED")
