"""Web UI tests: offline healthz shape when deps are unreachable; live stack is opt-in."""
import requests
import pytest

from agent.tools_zetaris import SqlError
from agent.web import healthz


def test_healthz_offline_unreachable(monkeypatch, tmp_path):
    def boom(_sql):
        raise SqlError("Zetaris request failed: connection refused")

    def fail(*_a, **_k):
        raise requests.ConnectionError("meterless unreachable")

    missing = str(tmp_path / "no-sample.json")
    monkeypatch.setattr("agent.web.run_sql", boom)
    monkeypatch.setattr("agent.web.requests.get", fail)
    monkeypatch.setenv("METERLESS_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setattr("agent.web.SAMPLE_PATH", missing)

    body = healthz()
    assert set(body) >= {"zetaris", "meterless", "sample", "status"}
    assert body["zetaris"] == "down"
    assert body["meterless"] == "down"
    assert body["sample"] == "missing"
    assert body["status"] == "degraded"
    assert body.get("reason")


@pytest.mark.live
def test_healthz_live_stack():
    body = healthz()
    assert set(body) >= {"zetaris", "meterless", "sample", "status"}
    assert body["zetaris"] == "ok"
    assert body["meterless"] == "ok"
    assert body["sample"] in ("present", "missing")
    assert body["status"] == "ok"
