# Open Agent Hackathon 2026 — rules + status log

> Build window: **Oct 22 00:00 → Oct 27 23:45 UTC** (hard submit). Judging Oct 28. Results **Nov 6, 16:00 UTC**.
> Registered as ffylaktis. Building **solo**, **Track 2**.

---

## Our status

**✅ Done**
- Zetaris (DATA) — running locally in Docker, 9/9 verify, sample data loaded (NY_TAXI, TPCDS_DB)
- NVIDIA Nemotron (POWER) — `nvidia/nemotron-3.5-lightning-30b-a3b`, direct route, key in `.env`
- Cursor installed
- Meterless Nightshift installed + running (port 8088)
- Agent loop proven end-to-end: Nemotron → run_sql tool-call → Zetaris → answer
- `smoke_test.py` → 3 PASS (Zetaris web, Zetaris SQL, Nemotron)

**🔨 To build (deadline Oct 27 23:45 UTC)**
1. The product — Track-2 evidence agent (Planner → Analyst → Evaluator → Reporter); register a free public health API (ClinicalTrials.gov / openFDA) into Zetaris; every claim traced to SQL; Evaluator rejects unsupported claims.
2. **Meterless Engine** (REQUIRED) — integrate H-Mem into a working feature (from meterless.ai/engines.html).
3. **Route through Nightshift** (REQUIRED for Power rule + DGX prize) — NVIDIA key in Nightshift → Providers; assign Lightning lane; Console Runtime URL + token → `.env` METERLESS_*.
4. Deliverables — demo video (1–4 min), slide deck, GitHub repo + README, sponsor-tech writeup.

---

## The mission
A working AI agent that does **real work** — accesses data, reasons across steps, maintains context, produces a useful outcome. Not a chatbot/UI demo. Solo or teams 1–5.

## Tracks (pick ONE; changeable until submit)
1. **Solving Fragmented Intelligence** — work across scattered/disagreeing sources
2. **The Agent That Can Explain Why** ← *ours* — investigate across sources, evidence-backed cited answers
3. **Reasoning Architecture** — data + knowledge + memory → reliable decisions/actions
- **Wildcard [Tinkerer]** — extend existing project; scored only on new work

## Mandatory tech (eligibility, not bonus)
- **Zetaris** — required in every submission; the data layer
- **Meterless** — (a) ≥1 Engine (H-Mem / Markovian / World Model / Scout Intent) in a *working feature*; (b) app calls **Nightshift** as a provider. Mentioning/unused dependency does NOT count.
- **Cursor** — required dev environment
- **NVIDIA Nemotron** — where it contributes; required for DGX Spark prize

## Strong vs weak agent
- **Strong:** dynamic delegation, agents critique/validate each other, Planner↔Executor↔Evaluator loops, shared memory, branching/retries/escalation, logs/traces of reasoning.
- **Weak:** linear A→B→C pipeline, no feedback, prompt-wrapper agents, hardcoded demo paths, no decision-making evidence.

## Submission (via HackOS)
1. **Demo video** 1–4 min — workflow, how it solves the track, Zetaris + Meterless integration
2. **Slide deck** — problem/users, solution, agent architecture, stack, sponsor-tech use + what was unique, visuals, future work
3. **GitHub repo** — all source + README (setup/usage/deps); Colab links if used
4. **Sponsor-tech writeup** — how Zetaris, Meterless, Cursor, NVIDIA each used

## Judging — 100 pts, ≥3 judges
| Criterion | Pts |
|---|---|
| Impact | 30 |
| Technical | 20 |
| Innovation | 15 |
| Demo | 15 |
| Product/UX | 10 |
| Sponsor Tech | 10 |

Ties: Impact, then submission timestamp.

## Hard rules
- Built **during the window** (Oct 22–27); declare pre-existing components in the form
- No committed secrets — `.env` gitignored, `.env.example` placeholders only
- Reproducible from a clean setup, no manual steps; keep repo light (samples not GB dumps)
- One account per person; duplicates disqualify the team; team locks at first submission
- Any language/framework/model; generated code allowed (you own it)

## Prizes
Up to $20K ($15K cash / $5K in-kind). Per track ~$2,000 / $1,350 / $1,000; Wildcard $1,000 / $600 / $400. Plus **NVIDIA DGX Spark** for best Nemotron use.

## Help
HackOS **#help desk** + per-sponsor Help channels; rules → hackathons@genai.works
