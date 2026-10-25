# Evidence-Intelligence Agent — Open Agent Hackathon 2026

**Track 02 · "The Agent That Can Explain Why."** An AI research analyst that answers clinical-evidence
questions **and shows its receipts** — grounded in live governed data, with an Evaluator that **deletes any
claim it can't back with evidence**.

> Demo question: *"What neuromodulation is being trialed for anorexia nervosa, and is any of it FDA-cleared
> for that use?"* → the agent reports what's **trialed** (ClinicalTrials.gov), reconciles it against what's
> **FDA-cleared** (openFDA), affirms the honest scoped conclusion (*trialed; none of the cleared neuro-device
> records reference anorexia*), and **rejects** the over-claim "rTMS is FDA-cleared for anorexia."

## What makes it a *real* agent (not a pipeline)
- **Specialized roles, separate model calls:** Planner → Analyst → cross_source → Reporter → **Evaluator**.
- **Feedback loop:** the Evaluator verifies every claim against *only its cited evidence* and rejects the
  unsupported; rejections are fed back and the Reporter revises (bounded rounds).
- **Self-consistency gate:** a would-be-"supported" verdict must pass a unanimous mini-panel (guards false positives).
- **Cross-source join (the innovation):** reconciles *trialed* (ctgov) vs *cleared* (openfda) + indication check.
- **Grounding:** every claim cites the exact SQL behind it; empty results are first-class "absence" evidence.
- **Shared memory:** H-MEM (the Meterless Engine) stores evidence with mandatory `source`/`provenance`/`confidence`.
- **Full trace + telemetry:** every step, verdict, route, token count, and Meterless receipt is recorded.

See `docs/architecture.md` for the diagram.

## Sponsor tech (how each is used → `docs/sponsor-tech.md`)
- **Zetaris** — the data layer. ClinicalTrials.gov + openFDA are registered as Lightning REST tables and
  queried with read-only SQL through one access point.
- **Meterless** — (a) **Engine:** a focused H-MEM port is the agent's evidence memory; (b) **provider:** every
  model call routes through **Nightshift** (`:8088`), returning signed receipts.
- **NVIDIA Nemotron** — the reasoning model, pinned (`nvidia/nemotron-3.5-lightning-30b-a3b`) via Meterless.
- **Cursor** — development environment.

## Prerequisites
- Python 3.12, Docker Desktop, 16 GB+ RAM.
- **Zetaris** running locally in Docker (`localhost:8888`) — see `HACKATHON.md` / Zetaris getting-started.
- **Meterless Nightshift** running (`127.0.0.1:8088`) with the NVIDIA provider + a Nemotron lane configured.

## Setup
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # Windows (openai, python-dotenv, requests)
cp .env.example .env                               # fill in the values below
```
`.env` keys: `ZETARIS_REST_URL, ZETARIS_ORG_ID=1, ZETARIS_API_KEY` · `METERLESS_BASE_URL=http://127.0.0.1:8088/v1,
METERLESS_RUNTIME_TOKEN, METERLESS_MODEL=meterless/auto` · `MODEL_BASE_URL, MODEL_API_KEY, NEMOTRON_MODEL` (NVIDIA fallback).

Register the data into Zetaris (idempotent), then verify the stack:
```bash
python -m data.register data/01_ctgov_register.sql       # ClinicalTrials.gov (anorexia) -> ctgov.*
python -m data.register data/02_openfda_register.sql     # openFDA AI devices -> openfda.ai_devices
python -m data.register data/03_openfda_neuro_register.sql# openFDA neuromod -> openfda.neuro_devices
python smoke_test.py                                      # 3 PASS = Data + Power layers live
```

## Usage
```bash
python -m agent.orchestrator "your clinical-evidence question"
python -m agent.orchestrator --record            # record a known-good run to data/sample_run.json
# SAMPLE_MODE=1 in .env  -> replay the recorded run instantly (bulletproof demo, no live calls)

# Web UI (zero extra deps — Python stdlib) — question in; cited answer, rejected claims, receipts out
python -m agent.web                              # -> http://127.0.0.1:7000  (⚡ instant replay, or ▶ run live)
```
## Dev / quality
```bash
ruff check .                      # lint (config in pyproject.toml)
pytest                            # offline unit tests (guard, H-MEM) — no stack needed
pytest --run-live                 # + live integration (needs Zetaris + Meterless up)
python -m evals.run_evals         # grounding scorecard vs the recorded sample (CI-safe)
python -m evals.run_evals --live  # score fresh live runs across the golden set
```
CI (`.github/workflows/ci.yml`) runs ruff + offline pytest + the sample scorecard on every push.

## Repo layout
```
agent/   orchestrator · planner · analyst · cross_source · reporter · evaluator · memory(H-MEM) · tools_zetaris · llm · trace · config
data/    *_register.sql recipes + register.py (privileged DDL path) + sample_run.json
evals/   grounding golden set + scorers + run_evals (sample & live scorecards)
tests/   pytest — offline (guard, H-MEM) + live-marked integration (tools, analyst, e2e)
docs/    architecture.md
pyproject.toml · requirements-dev.txt   # ruff + pytest config, dev tooling
PRD.md · DECISIONS.md · HACKATHON.md     # spec, decision log, rules
```

## Dependencies
Runtime: `openai==3.36.1`, `python-dotenv==1.2.4`, `requests==2.34.2` (`requirements.txt`).
Dev/quality: `ruff==0.17.2`, `pytest==9.1.1` (`requirements-dev.txt`). Zetaris + Meterless run as
external services (above). No secrets are committed; `.env` is gitignored.
