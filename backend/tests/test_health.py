"""Phase 0 acceptance: the app boots and /health answers 200.

`db` may legitimately be "down" (no Postgres in CI / bare unit runs) — the
endpoint reports connectivity honestly while still proving liveness.
"""

from app.main import app
from fastapi.testclient import TestClient


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] in {"up", "down"}
    assert body["env"]


def test_openapi_docs_served() -> None:
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
