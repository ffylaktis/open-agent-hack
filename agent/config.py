"""Central config — all tunables read from env (see .env / PRD §12)."""
import os

MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "3"))
MAX_SQL_RETRIES = int(os.environ.get("MAX_SQL_RETRIES", "2"))
MAX_STEPS = int(os.environ.get("MAX_STEPS", "6"))        # per-agent tool-loop cap
SQL_ROW_LIMIT = int(os.environ.get("SQL_ROW_LIMIT", "200"))
SAMPLE_MODE = os.environ.get("SAMPLE_MODE", "0").lower() in ("1", "true", "yes")
PINNED_MODEL = os.environ.get("METERLESS_MODEL_PINNED", "nvidia/nemotron-3.5-lightning-30b-a3b")
HMEM_PATH = os.environ.get("HMEM_PATH", "data/hmem_store.json")
