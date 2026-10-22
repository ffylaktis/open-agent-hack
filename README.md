# Open Agent Hackathon 2026 — starter

Build an agent that does real work. Three mandatory layers:

- **DATA — Zetaris** (local, in Docker) — the data your agent reasons over
- **BUILD — Cursor + ≥1 Meterless Engine** — where/what you build with
- **POWER — Meterless Nightshift + NVIDIA Nemotron** — what runs your product

## Project layout
```
open-agent-hack/
├── .env              # your secrets + settings (gitignored — copy from .env.example)
├── .env.example      # template
├── .gitignore        # lists .env
├── requirements.txt
├── smoke_test.py     # the pre-kickoff check (3 PASS lines = ready)
├── prompts/          # Meterless Engine prompt files
└── agent/
    ├── llm.py            # POWER: Nemotron client
    ├── tools_zetaris.py  # DATA: run_sql()
    └── main.py           # the agent loop
```

## Ready-for-kickoff checklist (tick all 7)
- [ ] **1. DATA** — Zetaris Cloud account + `zetaris-platform.zip` downloaded
- [ ] **2. DATA** — `./verify.sh` passes (9/9) and the Pikachu query returns 2 rows
- [ ] **3. DATA** — Zetaris API key created and saved in `.env`
- [ ] **4. BUILD** — Cursor installed, credit active, Agent prints "hello"
- [ ] **5. BUILD** — ≥1 Meterless Engine integrated in a working feature
- [ ] **6. POWER** — Nemotron route chosen; base URL + key + model id in `.env` (all same route)
- [ ] **7. ALL** — `.env` in `.gitignore`, and `smoke_test.py` → 3× PASS

## Setup order (start the slow one first)
1. **Zetaris (30–45 min download)** — register at `cloud.enterprise.zetaris.com/register`,
   download the bundle + registry sign-in from the **Run locally** page, then in a **WSL/Ubuntu** terminal:
   ```bash
   unzip zetaris-platform.zip && cd zetaris-platform
   docker login zetarishackathon.azurecr.io      # use the registry creds
   ./preflight.sh                                 # fix any FAIL before continuing
   # edit .env: set ZETARIS_ADMIN_EMAIL / _PASSWORD / _ORG, keep ZETARIS_SEED_TPCH=true
   docker compose pull && docker compose up -d
   ./verify.sh                                    # expect 9/9
   ```
   Then open http://localhost:3000, run `SELECT 1 AS one;`, do the PokéAPI recipe (Data 1.8),
   and create your API key → paste into `.env` here.
2. **Cursor** — install from `cursor.com/download`, sign in, confirm it can create+run a file.
3. **Meterless Nightshift** — download from `meterless.ai` (email gate), install, leave running.
4. **NVIDIA** — get a free key at `build.nvidia.com/models`, add it in Nightshift → Providers,
   assign a Nemotron model to a lane.
5. Pick your Nemotron route for `.env` (`MODEL_BASE_URL` / `MODEL_API_KEY` / `NEMOTRON_MODEL`).

## Run
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt     # Windows
python smoke_test.py                              # want 3 PASS lines
python -m agent.main "What's in the sample data?"
```

Deadlines (UTC): build opens 22 Oct 00:00 · **submit by 27 Oct 23:45** · results 6 Nov.
