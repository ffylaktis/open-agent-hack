# Session log — Evidence-Intelligence Agent

**Open Agent Hackathon 2026 · Track 02 ("The Agent That Can Explain Why")**
**Date:** 2026-10-25 · **Builder:** Fylaktis Fylaktou (UCLA Semel Institute) · **Snapshot HEAD:** `4a9b893`

An AI research-analyst agent that answers clinical-evidence questions, grounds every claim in governed
SQL, and **deletes any claim an independent Evaluator can't back**. Stack: **Zetaris** (data layer),
**Meterless** (H-MEM engine + Nightshift provider, signed receipts), **NVIDIA Nemotron** (reasoning), **Cursor**.

## What we did this session

### Agent — hardened + parallelized
- Full Track-2 loop: Planner → (Analyst × sub-questions ∥ cross_source) → Reporter → **Evaluator**, with a
  feedback loop (unsupported claims bounce back to the Reporter, ≤ MAX_ROUNDS) and a self-consistency gate.
  Every claim is bound to its SQL; absence / negative evidence is first-class.
- **Parallel sub-question fan-out** — each sub-question runs as its own concurrent agent into a shared,
  thread-safe H-MEM (locks on `MemoryStore.write` + `Trace.add`). Wall-clock = slowest sub-question, not the sum.
- Fixed 4 review findings: independent (temperature-sampled) Evaluator panel; Analyst must query before
  concluding; `run(allow_sample=…)` so "Run live" never silently replays; guard LIMIT literal-strip.

### Quality — tests, evals, CI
- **Ruff** (clean) · **pytest** with offline/`live` markers + conftest · **GitHub Actions CI**.
- **Eval harness** (`evals/`): golden set + structural grounding scorers + `run_evals` (sample & live);
  the recorded run scores **8/8**. Plus a concurrency regression test for the fan-out.

### Web UI
- Zero-dependency stdlib server (`agent/web.py`): question → cited answer + rejected panel + receipts;
  instant SAMPLE replay + Run-live toggle.

### Deliverables
- **Slide deck** (`deck/build_deck.py` → PPTX, 10 slides) — dark title/climax/closer, rebalanced bullets,
  real UI screenshots (captured via Playwright), sponsor logos, a ✓/✗ "receipt" stamp motif, and an
  architecture slide reworked into a **parallel fan-out with shared memory + feedback loop** (not a pipeline).
- **Demo-video script** (`docs/demo-script.md`) — NeuroOptimized to 74/100.
- **Judge Q&A cheat-sheet** (`docs/judge-qa.md`) — objection handling, each with the receipt to point at.
- **Sample re-recorded** on the parallel run (`data/sample_run.json`: meterless ×26, 52 trace steps, still 8/8).

## Current state
- Working tree clean at `4a9b893`; ruff clean; offline tests green; live e2e green; eval scorecard 8/8.
- Off-repo backup: `open-agent-hack-<timestamp>.bundle` in the home folder
  (restore with `git clone open-agent-hack-<timestamp>.bundle <dir>`).

## Remaining (yours)
- **Cursor** — ✅ done: Cursor's Composer agent implemented the `/healthz` stack-health endpoint
  (`agent/web.py`) + tests; `docs/sponsor-tech.md` describes the real usage (commit `96880a0`).
  All four sponsor techs (Zetaris · Meterless · Nemotron · Cursor) are now genuinely used.
- Record the demo video (script + SAMPLE replay).
- Push to GitHub + `git tag v1.0-submission`.
- Submit on HackOS (declare pre-existing OSS libs: openai / requests / python-dotenv).

## Commit trail (newest first, this build)
```
4a9b893 Regenerate deck pptx: parallel Slide 5 (label fix) + re-recorded hero
2e8adf4 Slide 5 as parallel gather lanes + re-record sample on the parallel run
4c3f437 Parallel sub-question fan-out: each sub-question runs as a concurrent agent
a79f631 Slide 5: left-to-right layout with a shared-memory lane + feedback loop
4b0fdf8 Slide 5: connect H-MEM (write/read spokes) — depict the shared-memory trait
fa599c4 Slide 5: ring/cycle layout so it can't read as a pipeline
5d7de5d Add judge Q&A cheat-sheet: objection handling with receipts
b1d1324 Deck: sponsor logo strip on slide 8
9756edd Deck redesign: dark climax + dark closer, rebalanced slides, stamp motif
b135141 Slide 5: draw the feedback loop so it reads as a cycle, not a pipeline
a4d7f21 Deck visuals: embed real UI screenshots on Slides 4 & 7
3531332 Deck polish: hanging-indent wrapped bullets + lift Slide 3
4460fdf Submission deliverables: slide deck (PPTX) + NeuroOptimized demo-video script
21e3844 Fix review findings 1-4: independent eval panel, analyst must query, live toggle, guard LIMIT
f39f53a Quality tooling: ruff + pytest (offline/live markers) + CI; lint-clean agent
96484bb Eval harness: grounding golden set + scorers + sample/live scorecard
964c057 Web UI (Product/UX): zero-dep stdlib server over the agent
2097779 End-to-end audit fixes (1-4)
a980895 Dedup fix + submission deliverables (README, sponsor writeup, slide outline)
0342911 Option B: scoped indication claim now assertable
170bf98 QA deep-dive fixes (1,2,3,5 + tune 4)
52ade2a Exhaustive AI-eng review: fixes 1-12
c52f515 Build steps 4-7: cross_source + Planner + Reporter + Evaluator + orchestrator (full agent, E2E green)
aa7644b Full-dive review fixes (SE 1-4)
```
