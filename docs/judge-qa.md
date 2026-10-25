# Judge Q&A cheat-sheet — Evidence-Intelligence Agent

Prep for live Q&A / the submission. Each answer is short and ends with the **receipt** to point at
(a file, a slide, or a demo action). Lead with honesty — the scrupulousness *is* the product.

## 30-second pitch
> In clinical/regulatory/pharma work, the blocker to AI isn't "can it answer" — it's "can you trust the
> answer." LLMs fabricate citations, and one wrong claim in medicine is disqualifying. This agent answers
> cross-source clinical-evidence questions, **binds every claim to the exact SQL behind it**, and runs a
> separate **Evaluator that deletes any claim it can't back**. It shows its receipts.

## The money moment (what to demo)
Hit **⚡ Instant replay** → scroll to the red **Rejected by the Evaluator** panel → it struck out
*"rTMS is FDA-cleared for anorexia"* with the reason → point to the **telemetry chips** (Meterless ×24,
signed receipts). That's the "explain why" in ten seconds.

---

## Is it a real agent? (Technical / Innovation)

**Q: Isn't this just a linear pipeline with fixed steps?**
No — specialized roles each make separate Nemotron calls, and there's a real feedback loop: the Evaluator
bounces any unsupported claim back to the Reporter, which revises & re-cites, looping ≤ MAX_ROUNDS. There's
branching (supported → ship, unsupported → revise), per-step error handling, and bounded SQL retries.
*Point to:* slide 5 (the drawn loop), `agent/orchestrator.py`, the 45-step trace in the UI.

**Q: Isn't this just RAG with extra steps?**
RAG retrieves then generates and trusts the generation. Here retrieval is **governed SQL** (not embeddings),
every claim is bound to the query that produced it, and an independent Evaluator — seeing only a claim's own
cited evidence, never the transcript — deletes anything unsupported. Absence/negative evidence is first-class.
Verification-first, not retrieval-first.
*Point to:* `agent/evaluator.py` (isolated input), `agent/memory.py` (provenance contract), the rejected panel.

**Q: The "self-consistency panel" — real, or theater?**
Real. The primary verdict is deterministic (temp 0); the re-check votes sample at temperature > 0 so they're
genuinely independent, and a claim survives only on unanimous agreement. (We caught and fixed an earlier
version where every vote ran at temp 0 — that *was* theater.)
*Point to:* `agent/evaluator.py` (`EVAL_PANEL_TEMPERATURE`), `agent/config.py`.

## Data & methodology (Technical / Impact)

**Q: Your dataset is tiny (~100 trials, 25 devices). Cherry-picked?**
It's live, not a dump — the Zetaris Lightning REST tables re-query ClinicalTrials.gov and openFDA on demand,
so it generalizes to any condition; the eval harness runs a second condition (MDD). Scoped for reproducibility
and a clean story, not because it only works here.
*Point to:* `data/*.sql`, `evals/cases.py`, README.

**Q: openFDA 510(k) has no "indication" field — so "no record references anorexia" is weak.**
Correct — and that's exactly why the agent **scopes** the claim ("among the records searched…") and the
Evaluator **rejects** the universal negative. The honesty about the bound is the feature, not a gap.
*Point to:* `agent/cross_source.py` (epistemic note), the rejected over-broad negatives, slide 7.

**Q: How do I know it isn't hallucinating the SQL or the numbers?**
Every claim cites the exact SQL string captured at execution (stored in H-MEM provenance); the content lines
are code-generated from `len(rows)`, not LLM free-text; the Evaluator grades against the real rows. Click any
citation chip to see the query.
*Point to:* `agent/tools_zetaris.py`, `agent/analyst.py` / `cross_source.py`, the citation chips.

## Sponsor tech (Sponsor)

**Q: Is the sponsor tech load-bearing or bolted on?**
Remove any one and it breaks. Data access is *only* via Zetaris SQL (one access point + read-only guard);
H-MEM *is* the evidence memory (the provenance contract); every model call routes through Meterless Nightshift
and returns a **signed receipt** (we surface receipts + telemetry per run); Nemotron does the adjudication.
*Point to:* slide 8, `docs/sponsor-tech.md`, the telemetry chips.

**Q: Did Nemotron actually contribute?**
It's the reasoning model for the judgment roles (planner/reporter/evaluator) and function-calling for the
analyst's SQL — the accept/reject decisions are Nemotron's. Pinned model; receipts prove the route.
*Point to:* `agent/llm.py`, `docs/sponsor-tech.md`.

## Product, market, impact (Impact / Product-UX)

**Q: Who uses this and pays?**
Clinical/regulatory evidence teams, pharma competitive-intelligence, medical-affairs/HEOR — they do slow,
manual evidence synthesis across fragmented registries today. The wedge is trust/verification infrastructure.
*Point to:* slide 2.

**Q: Is this clinical decision-making / medical advice?**
No. It's a research/evidence-intelligence tool for professionals; it reports what's trialed vs. cleared and
refuses to assert beyond the data. No treatment recommendations, not a clinical device.

**Q: What's the moat? Couldn't I just prompt GPT to do this?**
The moat is the verification layer + governed cross-source joins + provenance, not the prompt. A one-shot LLM
can't bind claims to queries, can't reject its own unsupported claims from an isolated view, and gives you no
auditable receipts. Trust infrastructure compounds with data partnerships.

## Reproducibility & rigor (Technical / Demo)

**Q: Can we run it? Is the demo real or hardcoded?**
Real — live against Zetaris + Meterless. For a fast, deterministic demo we replay a *captured real run*
(SAMPLE_MODE / the UI's instant replay); "Run live" runs it fresh. Nothing is hardcoded.
*Point to:* README (SAMPLE_MODE), `agent/orchestrator.py` (record/replay), the UI "Run live" toggle.

**Q: What proves it works beyond one demo?**
ruff-clean · GitHub Actions CI · 15 offline unit tests + live integration tests · an eval harness that scores
grounding invariants — the recorded run passes **8/8** (cross-source present, every claim cited, citations
resolve, negatives scoped, overclaim rejected, Meterless route, receipts).
*Point to:* `evals/`, `tests/`, `.github/workflows/ci.yml`, slide 9.

**Q: Limitations / what next? (answer this honestly)**
Two public sources and a scoped dataset; openFDA has no indication field (bounds the negative); the eval
scorers are structural, not a full faithfulness suite; live latency ~2–3 min. Next: richer indication signal
(device classification/product codes), more sources, a multi-judge panel, live on-demand source registration.
*Point to:* slide 10.

---

## Don't (overclaim traps)
- Don't say it's **deployed in hospitals** or **informed patient care** — it hasn't been.
- Don't call it a **clinical device** or imply medical advice — it's an evidence/research tool.
- Don't claim **customers or revenue** — it's a working prototype + a validated hypothesis.
- Don't oversell the dataset — say "live REST tables, scoped demo," not "comprehensive."
- When unsure, **lean into the honesty** — "the agent refuses to assert that" is the whole pitch.
