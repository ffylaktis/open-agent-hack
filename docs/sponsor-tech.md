# Sponsor-technology writeup (§6.4)

How each sponsor technology is integrated, and what was unique about our use.

## Zetaris — the data layer (required)
- **How:** ClinicalTrials.gov v2 and openFDA 510(k) are registered as **Lightning REST tables** with
  `CREATE LIGHTNING REST TABLE` + `SCHEMASTORE VIEW`s that flatten nested JSON (`LATERAL VIEW explode`), giving
  `ctgov.trials`, `ctgov.interventions`, `openfda.ai_devices`, `openfda.neuro_devices`. Recipes in `data/*.sql`.
- **In the agent:** the only data access is `agent/tools_zetaris.py` → Zetaris REST `/sql-editor/sqls/run`. The
  agent reasons over **live** governed data (REST tables re-query the source), queried with one SQL dialect from
  one access point — exactly Zetaris's "query everything as SQL" value.
- **Unique:** (1) a hard **read-only guard** (SELECT/SHOW/DESCRIBE only; DDL goes through a separate privileged
  path) so the LLM can't mutate the instance; (2) a **cross-source SQL join of two disconnected registries**
  (trials × device clearances) — the Track-02 "work across multiple data sources" done in Zetaris SQL; (3) rows
  returned as dicts via the response `headers`, so every piece of evidence is self-describing and citable.

## Meterless — Engine + provider (required)
- **Engine (H-MEM):** `agent/memory.py` is a focused Python port of the Meterless **H-MEM** spec
  (`reference/meterless-hmem/AGENTS.md`): a canonical memory record with **mandatory `source`/`provenance`/
  `confidence`** (a record with no source is rejected by construction), tiered store, keyword/tag retrieval, and
  an append-only **trust ledger**. It is the agent's working evidence memory — not a bolt-on; the agent's
  "every claim traced to its query" guarantee *is* H-MEM's provenance contract.
- **Provider (Nightshift):** `agent/llm.py` sends every model call to **Meterless Nightshift** (`:8088`,
  OpenAI-compatible, headers `meterless-app`/`meterless-scope`), with direct-NVIDIA as a logged fallback.
- **Unique:** we capture the **signed Meterless receipt** (`routed_model`, `receipt_id`) on every call and
  surface aggregate **telemetry** (routes, tokens, receipts) in each run — provable, auditable routing.

## NVIDIA Nemotron
- **How:** the reasoning model is pinned to **`nvidia/nemotron-3.5-lightning-30b-a3b`**, reached *through*
  Meterless Nightshift (receipts prove the route), with reasoning explicitly enabled for judgment roles
  (Planner/Reporter/Evaluator) and disabled for the deterministic Analyst. Function-calling drives the Analyst's
  SQL tools; structured output (forced tool) drives Planner/Evaluator/Reporter.
- **Unique:** Nemotron does the actual adjudication — the **Evaluator** uses it to reject unsupported/over-broad
  claims, with a unanimous self-consistency panel guarding false positives.

## Cursor
- **Dev environment** for building and iterating on the agent. Concretely, **Cursor's Composer agent
  implemented the `/healthz` stack-health endpoint** (`agent/web.py`) and its tests — live reachability
  checks for Zetaris (a `SELECT 1` probe) and Meterless (a `/models` ping) plus demo-sample presence,
  returning a JSON status that never 500s. (Cursor is optional per §5.1.)

## One-line architecture
`Zetaris (governed SQL) → Nemotron via Meterless (reasoning + receipts) → H-MEM (evidence memory) → Evaluator gate`.
