# Slide deck outline (§6.2)

Target: 8–10 slides. Visuals pulled from `docs/architecture.md` and a recorded run (`data/sample_run.json`).

1. **Title** — "The Agent That Can Explain Why" · evidence-intelligence agent · Track 02 · one-line: *answers
   clinical-evidence questions and shows its receipts.*

2. **Problem & users** — LLMs fabricate clinical citations (19.9–91% in studies); evidence synthesis is slow and
   costly. Users: clinical/regulatory evidence teams who need an **auditable** answer, not a chatbot guess.

3. **The question (demo)** — *"What neuromodulation is trialed for anorexia nervosa, and is any FDA-cleared for
   that use?"* — a real cross-source question where the honest answer is nuanced.

4. **Solution** — an agent that gathers governed evidence, **cites the SQL behind every claim**, and an
   **Evaluator that deletes claims it can't back**. Show the answer: trial facts + scoped negative **affirmed**,
   and the over-claim "rTMS is FDA-cleared for anorexia" **rejected**.

5. **Agent architecture** — the diagram: Planner → Analyst (SQL tools) → cross_source (trialed × cleared) →
   Reporter (cited claims) → **Evaluator** (verify, reject, feed back) → H-MEM shared memory · trace.
   Emphasize: specialized roles, feedback loop, self-consistency gate — *not* a linear pipeline.

6. **The cross-source "explain why"** — ClinicalTrials.gov (trialed: tDCS/theta-burst/DBS) × openFDA (cleared
   neuro devices, Neurology/Cardio/Radiology — none reference anorexia). The reconciliation *is* the insight.

7. **The integrity moment** — the Evaluator rejecting the over-claim and the over-broad universal negatives,
   with its reasons. Screenshot the REJECTED block. This is the anti-hallucination story.

8. **Technical stack & sponsor tech** — Zetaris (governed SQL, read-only guard, cross-source join) · Meterless
   (H-MEM engine + Nightshift provider, **signed receipts**) · NVIDIA Nemotron (pinned, reasoning + tool-calls) ·
   Cursor. Show telemetry (routes/tokens/receipts) + a receipt id.

9. **What was unique** — claim-level citation binding, negative evidence, Evaluator self-consistency gate,
   H-MEM-as-evidence-memory, provable Meterless receipts, bulletproof `SAMPLE_MODE` replay.

10. **Future** — richer indication signal (device/classification), web UI, more conditions/sources, multi-judge
    panel, live on-demand source registration. (National-importance framing: trustworthy AI for clinical evidence.)
