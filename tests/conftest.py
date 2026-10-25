"""Shared pytest setup: put the repo root on sys.path, load .env, and define the `live` marker.

Tests marked `live` need the Zetaris + Meterless stack running; they are skipped unless you pass
--run-live or set RUN_LIVE=1 — so plain `pytest` (and CI) runs only the offline tests."""
import os
import sys

import pytest
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
load_dotenv(os.path.join(ROOT, ".env"))


def pytest_addoption(parser):
    parser.addoption("--run-live", action="store_true", default=False,
                     help="run tests marked 'live' (needs Zetaris + Meterless running)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live") or os.environ.get("RUN_LIVE"):
        return
    skip_live = pytest.mark.skip(reason="needs live stack; pass --run-live or set RUN_LIVE=1")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
