"""Accept test — Step 3: Analyst turns a sub-question into Evidence via Nemotron→Zetaris."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from agent.analyst import analyze
from agent.memory import MemoryStore
from agent.trace import Trace

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_hmem_analyst.json")

def main():
    if os.path.exists(TMP):
        os.remove(TMP)
    store = MemoryStore(path=TMP)
    trace = Trace()
    subq = {"question": "Which device interventions have been trialed for anorexia nervosa?", "source": "ctgov"}
    ev = analyze(subq, store, trace)
    print("--- trace ---")
    for line in trace.summary():
        print(" ", line)
    print(f"evidence returned: {len(ev)}")
    if ev:
        e = ev[0]
        print("  source:", e.source, "| rows:", len(e.rows), "| route:", [x.get("route") for x in trace.events if x.get("route")][:1])
        print("  content:", e.content[:180])
        assert e.source in ("ctgov", "openfda"), "bad source"
        assert e.provenance, "no provenance"
        assert e.rows, "no rows"
        print("PASS analyst produced grounded evidence")
    else:
        print("FAIL analyst produced no evidence")
    if os.path.exists(TMP):
        os.remove(TMP)

main()
