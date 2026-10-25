# PRD — Open Agent Hackathon 2026 build (v2, agent-engineered)

Single source of truth. Companions: `DECISIONS.md` (why), `HACKATHON.md` (rules+status), `reference/` (specs).
**Deadline 27 Oct 2026 23:45 UTC · Track 02 "The Agent That Can Explain Why" · solo.**

---

## 1. Product
AI research analyst that answers clinical-evidence questions and **shows its receipts** — grounded in live governed data, with an Evaluator that **deletes any claim it can't back with retrieved evidence.**
- **User:** clinical/regulatory evidence people needing an *auditable* answer.
- **Problem:** LLMs fabricate clinical citations (19.9–91%); synthesis is slow/costly. Trust is the gap.
- **Wedge:** autonomic/interoceptive & neuromodulation evidence (founder's domain).

## 2. Demo question (the thing judges see)
**"What neuromodulation is being trialed for anorexia nervosa, and is any of it FDA-cleared for that use?"**
Expected truthful answer: rTMS/theta-burst/tDCS/DBS **trialed** (CT.gov NCTs) · neurostim/cardiac/wearable devices **cleared but for other indications** (openFDA) → **trialed YES / cleared-for-AN NO.** Evaluator rejects the seeded overclaim *"rTMS is FDA-cleared for anorexia."*

## 3. Requirements coverage
| Requirement | Satisfied by | Status |
|---|---|---|
| Zetaris | data layer `ctgov.*`+`openfda.*` via `run_sql` | ✅ |
| Meterless provider | Nemotron via Nightshift `:8088` (receipt) | ✅ proven / wire `llm.py` |
| Meterless Engine (req) | **H-MEM** evidence memory | 🔨 |
| NVIDIA | Nemotron reasoning+tools; receipt=DGX | ✅ |
| No secrets / reproducible | `.env` gitignored; `data/*.sql`+`smoke_test.py` | ✅ |
| Strong agent (not pipeline) | roles + feedback/retry/branch + shared memory + trace | 🔨 |
| Multi-source | CT.gov × openFDA join | 🔨 |
| Video/slides/repo/writeup | deliverables | 🔨 |

## 4. Architecture
```
Q → PLANNER → sub-questions[+source]        [delegation/branching]
  → ANALYST  SQL → run_sql → rows → H-MEM    [tool use + shared memory]
  → CROSS_SOURCE trialed×cleared             [innovation + indication-mismatch flag]
  → REPORTER draft claims (each w/ evidence_ids)
  → EVALUATOR per claim, isolated input → verdict; unsupported → bounce  [critique/retry]
  → loop ≤ MAX_ROUNDS → finalize; rejected claims shown dropped  [escalation/recovery]
  trace.py logs every event; Meterless receipt captured
```
Model: Nemotron pinned via Meterless, **temperature 0** (Analyst/Evaluator), separate call per role.

## 5. Data contracts (typed state between agents)
```python
Evidence  = {id, content:str, type:"factual", source:"ctgov"|"openfda",
             provenance:{sql:str, retrieved_at:str}, confidence:float,
             tags:[str], entities:[str], layer:"working", rows:list}   # H-MEM record (minimal)
SubQ      = {id, question:str, source:"ctgov"|"openfda"|"cross", status:"open"|"done"|"failed"}
Claim     = {id, text:str, evidence_ids:[str]}        # evidence_ids REQUIRED
Verdict   = {claim_id, supported:bool, reason:str, missing:str|None}
TraceEvent= {t, step:int, agent:str, action:"plan"|"sql"|"tool_result"|"claim"|"verdict"|"final",
             payload, tokens?:int, latency_ms?:int, route?:str, receipt_id?:str}
```
**Citation-binding rule (core anti-hallucination):** a Claim with empty `evidence_ids`, or whose cited Evidence the Evaluator finds non-supporting, is **dropped**. No evidence → no claim.

## 6. Agent + tool contracts
- **Planner** — in: question. out: `[SubQ]` (structured). Picks source per sub-q; may add a `cross` sub-q.
- **Analyst** — in: SubQ + schema hints. out: tool call(s) `run_sql`; converts rows → `Evidence` (sets source, provenance.sql, confidence). Retries bad SQL ≤`MAX_SQL_RETRIES` using the error text.
- **Evaluator** — in: **only** `{claim.text, [evidence.content for cited ids]}` (NOT the transcript) → out: `Verdict` (structured). **Defaults to `supported:false`** if evidence is absent/ambiguous. Separate Nemotron call so it cannot rubber-stamp.
- **Reporter** — in: supported claims + evidence. out: final answer; every sentence cites evidence; rejected claims listed as "unsupported — dropped".
- **Tools** (`tools_zetaris.py`):
  - `run_sql(sql)` — **read-only guard**: allow only `SELECT/SHOW/DESCRIBE/WITH`; reject others. Strip trailing `;`. Inject `LIMIT SQL_ROW_LIMIT` if absent. 60s timeout. On error → `{error}` returned (fed back to Analyst).
  - `search_trials(cond, intr?)` → trials view rows. `search_devices(term)` → openFDA rows.
  - `cross_source(condition)` → see §7.

## 7. Cross-source join algorithm (the innovation)
1. From `ctgov.interventions` (type=DEVICE) for the condition → intervention names.
2. Normalize to modality terms (rTMS/theta-burst→"transcranial magnetic", tDCS→"transcranial direct current", DBS→"deep brain"/"neurostimulator", VNS→"vagus").
3. `search_devices(term)` on openFDA per modality → clearances (device_name, applicant, product_code, specialty).
4. Match trialed modality ↔ cleared device by normalized term.
5. **Indication check:** cleared-for (panel/specialty/device_name) vs trial condition (anorexia). Mismatch → Evidence tagged `indication_mismatch`. This drives the Evaluator's rejection of "cleared for anorexia".

## 8. H-MEM (focused Python port = the Meterless Engine)
- **Record:** §5 Evidence (mandatory `source`,`confidence`,`provenance` — record with no `source` rejected by construction, per spec).
- **Services:** `MemoryStore` (tiered dict/sqlite, `working` layer) · `MemoryRetrieval` (keyword+tag+entity match; **no embeddings** — set is small) · `TrustLedger` (append-only audit of every write/supersede).
- **Feature test (accept):** write evidence in run A; new run B retrieves it by tag/entity → proves persistent recall. (Not the full TS conformance.)

## 9. Provider (`llm.py`)
`chat(messages, tools=None, temperature=0)` → **primary: Meterless** (base/token + headers `meterless-app`,`meterless-scope:user`, model pinned `nvidia/nemotron-3.5-lightning-30b-a3b`); **fallback: direct NVIDIA** (`MODEL_*`) on Meterless error. Capture `receipt_id` from Meterless. Log route per call.

## 10. Control bounds & determinism
`MAX_ROUNDS=3` · `MAX_SQL_RETRIES=2` · `SQL_ROW_LIMIT=200` · global step cap ~20 agent calls · time budget ≤5 min · temperature 0 (Analyst/Evaluator). On cap hit → return best partial answer, flagged.
**`SAMPLE_MODE`**: record one known-good run to `data/sample_run.json` (ordered trace + final). Replay serves it with no live calls → bulletproof demo. Cache is of live data (refreshable).

## 11. Failure modes & recovery
| Failure | Handling |
|---|---|
| Source 4xx/5xx | retry once; else mark SubQ `failed`, continue |
| Empty rows | state "no evidence found" — never fabricate |
| SQL error | feed error to Analyst, ≤2 retries, else drop SubQ |
| Model returns no tool_call | re-prompt once with explicit tool instruction |
| Evidence insufficient after rounds | Reporter outputs "insufficient evidence" (graceful) |
| Meterless down | fallback to direct NVIDIA; log route |
| Runaway (steps/time/tokens) | abort → partial answer + flag |

## 12. Config / env
`ZETARIS_REST_URL, ZETARIS_ORG_ID, ZETARIS_API_KEY` · `METERLESS_BASE_URL, METERLESS_RUNTIME_TOKEN, METERLESS_MODEL` · `MODEL_BASE_URL, MODEL_API_KEY, NEMOTRON_MODEL` (fallback) · `SAMPLE_MODE, MAX_ROUNDS, MAX_SQL_RETRIES, SQL_ROW_LIMIT`.

## 13. Build plan (each = committed increment + executable accept test in `tests/`)
1. **`tools_zetaris` hardening** — read-only guard, strip `;`, LIMIT, curated tools. *Accept:* rejects a non-SELECT; device-interventions query returns rows.
2. **`memory.py` (H-MEM)** — record+Store+Retrieval+TrustLedger. *Accept:* recall feature-test passes; record without `source` rejected.
3. **Analyst** — SubQ→SQL→Evidence (+retry). *Accept:* returns Evidence for the neuromod query; recovers from one bad SQL.
4. **cross_source** — §7. *Accept:* returns trialed×cleared with ≥1 `indication_mismatch`.
5. **Planner** — Q→[SubQ]. *Accept:* demo Q → ≥2 sourced sub-qs + a `cross`.
6. **Evaluator** — isolated verdict. *Accept:* rejects seeded overclaim, keeps a supported claim.
7. **Reporter + orchestrator** — loop/bounds/trace. *Accept:* full demo Q → cited answer, overclaim shown dropped, trace emitted.
8. **`llm.py` → Meterless** + receipt. *Accept:* end-to-end routes via `:8088`, receipt saved.
9. **(later)** UI · SAMPLE_MODE record · demo video · slides · README · sponsor writeup.

## 14. Judging levers
Impact 30 · Technical 20 · Innovation 15 · Demo 15 · Product/UX 10 (UI later) · Sponsor 10. Separate: **DGX** = best Nemotron use (receipt).

## 15. Out of scope (weekend)
Full 7-service H-MEM TS conformance · embeddings/vector store · dynamic multi-condition registration beyond demo set · business buyer-validation (desk-only, deferred).
