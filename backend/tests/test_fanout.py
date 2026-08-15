"""Integration: the fan-out worker job — chunked sends, metrics, token hygiene.

Uses the LogPushSender fallback (no Firebase credentials in tests): the job
still exercises device lookup, payload assembly, delivery-metric persistence,
and UNREGISTERED pruning (verified via a fake sender).
"""

import asyncio
import uuid

from app.worker import fan_out_sos

from tests.conftest import auth_headers, register_user, set_location

VICTIM = {"lat": 22.5726, "lon": 88.3639}


def _setup(client, with_device: bool):
    victim = register_user(client, email="fan-victim@nearhelp.dev")
    responder = register_user(client, email="fan-responder@nearhelp.dev")
    set_location(client, victim["access_token"], VICTIM["lat"], VICTIM["lon"])
    set_location(client, responder["access_token"], VICTIM["lat"] + 0.001, VICTIM["lon"])
    if with_device:
        posted = client.post(
            "/api/users/me/fcm-token",
            headers=auth_headers(responder["access_token"]),
            json={"device_id": "device-fan-0001", "fcm_token": "token-fanout-00000001"},
        )
        assert posted.status_code == 204
    sos = client.post(
        "/api/sos/create",
        headers={**auth_headers(victim["access_token"]), "Idempotency-Key": uuid.uuid4().hex},
        json={"lat": VICTIM["lat"], "lon": VICTIM["lon"], "crisis_type": "medical"},
    )
    return sos.json(), responder


def test_fan_out_records_delivery_metrics(client, db_clean):
    body, responder = _setup(client, with_device=True)

    result = asyncio.run(fan_out_sos({}, str(body["id"]), 0, [responder["user"]["id"]]))
    assert result["sent"] == 1
    assert result["failed"] == 0

    timeline = client.get(
        f"/api/sos/{body['id']}/timeline", headers=auth_headers(_login(client))
    ).json()
    pushed = [
        e
        for e in timeline
        if e["event_type"] == "responders_notified" and e["details"].get("pushed")
    ]
    assert len(pushed) == 1
    assert pushed[0]["details"]["devices"] == 1
    assert pushed[0]["details"]["sent"] == 1
    assert "fanout_ms" in pushed[0]["details"]


def test_fan_out_without_devices_reports_zero_sends(client, db_clean):
    body, responder = _setup(client, with_device=False)
    result = asyncio.run(fan_out_sos({}, str(body["id"]), 0, [responder["user"]["id"]]))
    assert result["sent"] == 0


def test_unregistered_tokens_are_pruned(client, db_clean, monkeypatch):
    from app.services import notify as notify_module

    body, responder = _setup(client, with_device=True)

    class FakeSender:
        async def send_tokens(self, tokens, data):
            # Every token reports as dead — FCM's UNREGISTERED case.
            return {"success": 0, "failure": len(tokens), "unregistered": list(tokens)}

    monkeypatch.setattr(notify_module, "_sender", FakeSender())
    result = asyncio.run(fan_out_sos({}, str(body["id"]), 0, [responder["user"]["id"]]))
    assert result["pruned"] == 1

    # The stale device row is gone: "notified 1 responder" stays honest.
    remaining = _scalar("SELECT COUNT(*) FROM user_devices")
    assert remaining == 0


def _login(client) -> str:
    login = client.post(
        "/api/auth/login", json={"email": "fan-victim@nearhelp.dev", "password": "secret123"}
    )
    return login.json()["access_token"]


def _scalar(query: str):
    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        return conn.execute(text(query)).scalar_one()
