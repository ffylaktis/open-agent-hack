"""Central config — all tunables read from env (see .env / PRD §12)."""
import os

MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "2"))       # plan->report->evaluate->re-report rounds
MAX_SQL_RETRIES = int(os.environ.get("MAX_SQL_RETRIES", "2"))
MAX_STEPS = int(os.environ.get("MAX_STEPS", "6"))        # per-agent tool-loop cap
MAX_SUBQUESTIONS = int(os.environ.get("MAX_SUBQUESTIONS", "4"))
MAX_CLAIMS = int(os.environ.get("MAX_CLAIMS", "6"))
EVAL_PANEL = int(os.environ.get("EVAL_PANEL", "3"))      # self-consistency votes on would-be-supported claims
RUN_BUDGET_SECONDS = int(os.environ.get("RUN_BUDGET_SECONDS", "300"))
SQL_ROW_LIMIT = int(os.environ.get("SQL_ROW_LIMIT", "200"))
SAMPLE_MODE = os.environ.get("SAMPLE_MODE", "0").lower() in ("1", "true", "yes")
SAMPLE_PATH = os.environ.get("SAMPLE_PATH", "data/sample_run.json")
PINNED_MODEL = os.environ.get("METERLESS_MODEL_PINNED", "nvidia/nemotron-3.5-lightning-30b-a3b")
HMEM_PATH = os.environ.get("HMEM_PATH", "data/hmem_store.json")
