# Decision log — Open Agent Hackathon build

Running record of what we decided and why. Newest context at top of each section.

---

## 0. Final direction (decided)

**Build:** an **evidence-intelligence agent for digital-health / AI medical products** — "what's FDA-cleared, what's validated, on what evidence?" — on Track 02 ("The Agent That Can Explain Why").
**Beachhead:** **autonomic / interoceptive digital biomarkers** (the founder's expertise + the documented validation gap).
**Architecture:** Planner → Analyst(SQL) → **Evaluator (rejects unsupported claims)** → Reporter; Meterless **H-Mem** carries evidence across steps; **Nemotron** reasons; **Zetaris** is the data layer.
**Demo framing:** run the B2B product on a high-impact *health* question (e.g. dysautonomia / anorexia biomarker validation) so judges feel Impact while the product stays the defensible business.

**Goal weighting (founder):** NIW and venture **equally** · revenue **in scope** · could **become a real focus**.

---

## 1. Idea funnel (how we got here)

1. Started: generic "clinical-research evidence agent" (my proposal, built to Track 02 + founder's clinical field — not from any prior doc).
2. Expanded to 10 business ideas, then **re-framed 10 for NIW**.
3. Founder kept **#1 Veterans PTSD, #7 Suicide synthesis, #2 Youth MH, #6 Maternal MH**; asked for 10 more.
4. Second 10 (#11–20) split into: (A) named-priority evidence agents, (B) biosignal/neurotech "moat" plays.
5. VC triage → the **intersection picks**: **#16 Long-COVID dysautonomia, #17 digital-biomarker validation, #18 FDA/SaMD device intelligence**.
6. Verdict: **merge #17 + #18** = only option ★★★★+ on *both* axes. #16 = best NIW/mission but no clear payer → kept as mission artifact, not the company. Tier-C (#1/#7/#2/#6) = strong NIW, "feature-not-company" risk (OpenEvidence/Elicit own it).

---

## 2. NIW rationale (why this aligns)

- USCIS 2022 STEM NIW policy anchors "national importance" to the federal **Critical & Emerging Technologies (CET)** list. [IFP](https://ifp.org/bolstering-stem-talent-with-the-national-interest-waiver/)
- The chosen idea hits **3 CET categories**: Artificial Intelligence, Human-Machine Interfaces (neurotech), Biotechnologies. [2024 CET List](https://bidenwhitehouse.archives.gov/wp-content/uploads/2024/02/Critical-and-Emerging-Technologies-List-2024-Update.pdf)
- "Well-positioned" = founder's literal research (physiological/autonomic biomarker validation, computational psychiatry).
- A **judged placement** in this competition is itself the NIW evidence lever (recognized-competition award).

---

## 3. VC validation (desk / secondary — NOT primary)

**Problem is real & costly:**
- Clinical LLMs fabricate **19.9%–91%** of citations; ~**146k** hallucinated citations in 2025 (12× rise). [the-decoder](https://the-decoder.com/ai-hallucinated-citations-are-creeping-into-papers-that-shape-clinical-guidelines-researchers-warn/)
- Systematic reviews cost **~$141k / 6–18 months**.

**Market/money exists:**
- FDA AI-device clearances: **335 in 2025, 1,451 cumulative**; 62% SaMD. [tracker](https://sequenex.com/fda-ai-medical-device-authorizations-analysis/)
- RWE + intelligence TAM **~$90B**; incumbents IQVIA, Clarivate/Cortellis, Veeva.
- Digital biomarkers **$5.8B (2025) → ~$35B (2035), ~20% CAGR**; pharma = 37% of spend. [market](https://finance.yahoo.com/healthcare/articles/digital-biomarkers-market-size-surpass-112800811.html)

**Honest gaps:** zero customer conversations; market numbers are analyst-report (secondary); specific buyer + willingness-to-pay untested; wedge is a hypothesis.

---

## 4. 3-assumption teardown (result: 2.5 / 3 confirmed on desk)

1. **Budget exists — ✅ CONFIRMED.** Cortellis contracts ~$68.5k median (to ~$74k); Clarivate enterprise avg ~$270k/yr, SMB ~$16.6k/yr. Timing: Cortellis **sold to Altaris Oct 6 2026** (incumbent in transition = opening). Caveat: that validates budget *in category*, not necessarily *our* buyer.
2. **Wedge — ✅ need confirmed / ⚠️ buyer list not yet.** Validation pain is named + regulator-recognized via the **V3 framework** (DiMe; cited by NIH/FDA/EMA). For HRV/autonomic: "verification established, analytical validation emerging, clinical validation **limited**" = the gap is exactly our lane. Remaining gap: a list of specific reachable buyers (needs outreach, not desk).
3. **Public data enough — ✅ CONFIRMED.** CT.gov (in Zetaris) answered who's-developing / interventions / maturity. openFDA device 510(k) structured + searchable: **108 AI-named clearances** (e.g. Caption Health). Covers "what's cleared, by whom, what trials, what phase."

**Bottom line:** category has money, need is documented + regulator-recognized, data covers it. The one unresolved leap — *will a specific buyer pay?* — structurally needs outreach (deferred by founder). For the hackathon: green-lit. For the business: strong signal, one honest untested gate.

---

## 5. IP / rights decision (from binding Official Rules §05/§06/§09)

- **§9.1 — founder keeps all rights; nothing transfers to organizer/sponsors.** Own 100% (code + idea).
- **§9.2/9.3 — only a non-exclusive *promotional* license** (demo/screenshots/description) to organizer + track sponsor. Not code, not commercial rights.
- **§6.3 — repo required with all source, but NO public/open-source-license requirement.** → not forced to open-source the moat.
- **§5.1 — Zetaris + Meterless mandatory; Cursor OPTIONAL;** NVIDIA where it helps; **§5.5 generated code = you own it.**
- **Decision:** keep submission repo **private, grant judges access**; keep the real moat (proprietary data structuring, vertical logic, future private code) **out of the submitted repo**.

---

## 6. Data (state)

- **Live in Zetaris:** ClinicalTrials.gov v2 → `CTGOV_REST.an_studies`, views `ctgov.trials` + `ctgov.interventions` (100 anorexia-nervosa trials). Recipe: `data/01_ctgov_register.sql` + `data/register.py`.
- **Live in Zetaris (added):** openFDA device 510(k) -> `OPENFDA_REST.ai_510k`, view `openfda.ai_devices` (100 AI-named clearances; recent real ones e.g. GE Lung Guidance 2026-10, ThinkSono). Recipe: `data/02_openfda_register.sql`. (Fix noted: parentheses in a DESCRIBE BY string 400'd; keep descriptions alphanumeric.)
- **Optional later:** openFDA labels + FAERS; more CT.gov conditions (dysautonomia, Long COVID).
- All public / free / reproducible → data is **not** the moat (moat = depth + Evaluator + structuring).

---

## 7. Open loops / next

- [x] Register openFDA into Zetaris (Step 1b). ✅ done
- [ ] Build Analyst → Evaluator loop with **cross-source join** (Steps 2–5).
- [ ] Integrate Meterless H-Mem (Step 6, required).
- [x] Meterless Nightshift route LIVE ✅ — `POST :8088/v1/chat/completions` routes to `nvidia/nemotron-3.5-lightning-30b-a3b` and returns a signed `meterless.compute_receipt.v1`. `METERLESS_*` in `.env` (base `http://127.0.0.1:8088/v1`, token, `meterless/auto`); NVIDIA key added in Nightshift → Providers. **Remaining code task:** point `agent/llm.py` at the Meterless route (base_url=METERLESS_BASE_URL, token, default_headers `meterless-app`+`meterless-scope:user`, model `meterless/auto`) — the receipt = DGX-prize evidence.
- [ ] Minimal UI (not CLI), scripted 2-min demo, slides, README, sponsor writeup (Step 8).
- [ ] **Business-only, deferred:** buyer map + willingness-to-pay via outreach (the one untested gate).

**Deadline:** submissions close **Oct 27, 2026, 23:45 UTC**.

---

## 8. Rubric → build decisions (how we win each non-Impact criterion)

Both data sources now live in Zetaris (`ctgov.trials`, `ctgov.interventions`, `openfda.ai_devices`), which unlocks Track-02's "multiple data sources" literally.

- **Technical (20):** Planner → Analyst → **Evaluator** with real feedback/retry (Evaluator bounces an unsupported claim → Analyst re-queries); SQL errors fed back to the model; structured trace output; SAMPLE_MODE fallback.
- **Innovation (15):** two signatures — (1) Evaluator **deletes unsupported claims**; (2) **cross-source join** — "has this biomarker/intervention been both *trialed* (CT.gov) AND *cleared* (openFDA)?" This join is the reason openFDA was added.
- **Demo (15):** ≤2-min scripted, one killer question, show the Evaluator **reject a weak claim live** + the cross-source cited answer + a trace.
- **Product/UX (10):** minimal **web UI** (FastAPI + simple page), not CLI. **DECISION PENDING founder's yes** — costs ~hours, buys ~25 pts across UX + Demo.
- **Sponsor tech (10):** Zetaris central (multi-source SQL) ✅; Meterless **H-Mem** carries accumulated evidence across turns (required); Nemotron visible reasoning → also targets the **DGX Spark** prize.
- **Impact (30):** B2B product **demoed on a high-impact health question** (dysautonomia / anorexia biomarker validation) so judges feel impact while the product stays the defensible business.

**Verified facts worth not re-deriving:** openFDA returns ~108 AI-named 510(k) clearances; CT.gov AN set = 100 trials (25 device / 15 drug / 50 behavioral; 44 completed). Cortellis contracts ~$68.5k median (Cortellis sold to Altaris 2026-10-06). V3 validation framework (DiMe) = the regulator-recognized biomarker-validation standard; HRV/autonomic clinical validation is "limited" = the wedge.

---

## 9. Verified technical findings (2026-10-24)

**Tool-calling survives the Meterless→Nemotron hop — the key build risk is cleared.** Probe across 4 routes (same `run_sql` tool + "count ctgov.trials" prompt), all returned a valid tool call with correct SQL:
- DIRECT-NVIDIA → ✅ (also emits `reasoning_content`).
- METERLESS `auto` → ✅, and **no `reasoning_content` leaked** (Meterless handles it — cleaner to consume).
- METERLESS pinned `nvidia/nemotron-3.5-lightning-30b-a3b` → ✅ (Meterless accepts a pinned provider-model id → lets us force Nemotron for an unambiguous DGX receipt).
- METERLESS `auto`, `enable_thinking:false` → ✅.

**Decisions from this:**
- Agent routes through **Meterless, pinned to the Nemotron model** → Power rule + DGX receipt + no reasoning-content parsing.
- **`run_sql` must strip a trailing `;`** before sending to Zetaris (model sometimes appends one; Zetaris = one statement/call, no trailing semicolon).
- Probe: `scratchpad/toolcall_probe.py`.

**Killer demo question (from a data probe, 2026-10-24):** *"What neuromodulation is being trialed for anorexia nervosa, and is any of it FDA-cleared for that use?"*
- CT.gov AN device interventions are real neuromodulation: rTMS, theta-burst stimulation, tDCS, deep brain stimulation (NCT03984344, NCT02702167, NCT04846517, NCT02263404, NCT02734108).
- openFDA clearances exist for neurostim/cardiac/wearable (heart-rate 808, ECG 154, neurostimulator 12, wearable 82) **but for other indications, not anorexia.**
- Honest answer = trialed YES / cleared-for-AN NO → the **Evaluator rejects the overclaim "cleared for anorexia"** = the cross-source "explain why" moment. In-domain for the founder.

**Real-time data (confirmed):** Zetaris REST tables call the live API per query (not a snapshot), but each table is pinned to a fixed endpoint/condition at creation. Options: (A) agent registers sources on demand = truly real-time + general but slow/riskier live; (B) curated pre-registered + `CACHE TABLE`; (C) B for the recorded demo + one live on-demand registration as a flourish. **Leaning C.** Cache is of live data (refreshable), so the "real-time" story holds while the demo stays fast (`CACHE TABLE` 49.7s→1.2s) + `SAMPLE_MODE` fallback.

**API query syntax (openFDA, retrieved):** `search=field:value`, AND/OR, quoted phrases, `.exact`, date ranges, `count=` aggregation, `limit`/`skip`; endpoints `device/classification`, `device/pma`, `device/event` (MAUDE), `drug/label`, `drug/event` (FAERS). CT.gov v2 working params already known: `query.cond`, `query.intr`, `pageSize`, `fields`.

---

## 10. Build + QA complete (status, 2026-10-24)

Full agent built (Steps 1–8) and hardened over 4 review rounds (~35 issues) + an empirical QA pass; 15 unit tests + E2E green. Key outcomes:
- **Pipeline:** Planner → Analyst → cross_source → Reporter → **Evaluator** (verify → reject → re-report feedback loop, bounded by MAX_ROUNDS=2) + self-consistency panel (EVAL_PANEL=2, unanimous, guards false positives).
- **Grounding:** citation binding (every claim cites evidence_ids → the exact SQL); empty results stored as first-class absence evidence; **Option B** — indication evidence states the verified scoped fact (not an over-hedge), so the scoped negative is assertable while universal negatives + the rTMS over-claim are rejected.
- **Sponsor tech:** Zetaris (read-only guard + admin DDL split; cross-source SQL join); Meterless H-MEM port (atomic, deduped, mission-scoped) + Nightshift route with signed receipts; pinned Nemotron; reasoning explicitly enabled for judgment roles.
- **Robustness/observability:** phase-level error handling (no single blip crashes a run); run budget guards gather + evaluate; telemetry (routes/tokens/receipts) counts all calls incl. Evaluator; `SAMPLE_MODE` records/replays a bulletproof demo (`data/sample_run.json`).
- **Hygiene:** `.env`/`.venv`/`reference/` gitignored + untracked; no secrets in tracked files; deps pinned; dead `main.py`/`DISPATCH` removed; tests assert counts (not brittle exact live values).
- **Remaining:** slide deck (outline done), demo video, HackOS submission (declare OSS libs), optional UI.
