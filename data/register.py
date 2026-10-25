"""Run a .sql recipe against Zetaris over REST, one statement at a time.

Usage:  python -m data.register data/01_ctgov_register.sql
Reproducible setup: re-running is safe-ish (CREATE will error if the object
exists; those are reported but not fatal to later statements).
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
from agent.tools_zetaris import run_sql  # noqa: E402


def statements(path: str):
    raw = open(path, encoding="utf-8").read()
    # strip full-line comments, then split on ';'
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    for stmt in "\n".join(lines).split(";"):
        if stmt.strip():
            yield stmt.strip()


def main(path: str):
    for i, stmt in enumerate(statements(path), 1):
        label = " ".join(stmt.split())[:70]
        try:
            run_sql(stmt)
            print(f"[{i}] OK    {label}")
        except Exception as e:
            print(f"[{i}] ERROR {label}\n        -> {str(e)[:200]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/01_ctgov_register.sql")
