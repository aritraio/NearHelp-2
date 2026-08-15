"""Integration: escalation — the durable tick (waves, radius growth, expiry).

Events are aged backwards via SQL, then the tick runs directly through the
internal endpoint (which also exercises the secret guard). One tick
fast-forwards overdue events through all due waves (catch-up), and the wave
CAS guarantees a second tick is a no-op.
"""

from app.core.config import get_settings

from tests.conftest import auth_headers, register_user, run_sql, set_location

VICTIM = {"lat": 22.5726, "lon": 88.3639}


def _create_aged_sos(client, age_seconds: int, drill: bool = False) -> str:
    victim = register_user(client, email=f"victim{age_seconds}{drill}@nearhelp.dev")
    responder = register_user(client, email=f"responder{age_seconds}{drill}@nearhelp.dev")
    set_location(client, victim["access_token"], VICTIM["lat"], VICTIM["lon"])
    # Responder far outside the initial 2 km ring but inside wave-2's 6 km.
    set_location(client, responder["access_token"], VICTIM["lat"] + 0.045, VICTIM["lon"])

    import uuid

    response = client.post(
        "/api/sos/create",
        headers={**auth_headers(victim["access_token"]), "Idempotency-Key": uuid.uuid4().hex},
        json={
            "lat": VICTIM["lat"],
            "lon": VICTIM["lon"],
            "crisis_type": "medical",
            "is_drill": drill,
        },
    )
    sos_id = response.json()["id"]
    run_sql(
        "UPDATE sos_events SET created_at = now() - make_interval(secs => :age) "
        "WHERE id = CAST(:sos_id AS uuid)",
        {"age": age_seconds, "sos_id": str(sos_id)},
    )
    return sos_id


def _tick(client) -> dict:
    response = client.post(
        "/internal/escalation/tick", headers={"X-Tick-Secret": get_settings().internal_tick_secret}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_tick_requires_secret(client):
    assert client.post("/internal/escalation/tick").status_code == 403
    assert (
        client.post(
            "/internal/escalation/tick", headers={"X-Tick-Secret": "wrong-secret"}
        ).status_code
        == 403
    )


def test_overdue_event_escalates_through_waves_in_one_tick(client, db_clean):
    sos_id = _create_aged_sos(client, age_seconds=100)

    summary = _tick(client)
    assert summary["wave1"] == 1
    assert summary["wave2"] == 1
    assert summary["wave3"] == 1

    wave, radius = _event_state(sos_id)
    assert wave == 3
    assert radius == 2000 * 2 * 3  # 12 km — both expansions applied

    # The far responder became reachable during wave expansion.
    assert _responder_notified(sos_id) is True

    # Timeline shows the whole escalation story.
    victim_token = _token_for(client)
    timeline = client.get(f"/api/sos/{sos_id}/timeline", headers=auth_headers(victim_token)).json()
    types = [event["event_type"] for event in timeline]
    assert "escalation_wave" in types
    assert "call_services_prompted" in types


def test_second_tick_is_noop_cas(client, db_clean):
    sos_id = _create_aged_sos(client, age_seconds=100)
    _tick(client)

    summary = _tick(client)
    assert summary == {"expired": 0, "wave1": 0, "wave2": 0, "wave3": 0}

    # And no duplicate timeline events were written.
    victim_token = _token_for(client)
    timeline = client.get(f"/api/sos/{sos_id}/timeline", headers=auth_headers(victim_token)).json()
    assert [e for e in timeline if e["event_type"] == "escalation_wave"].__len__() == 2


def test_fresh_events_are_untouched(client, db_clean):
    _create_aged_sos(client, age_seconds=5)  # below every threshold
    summary = _tick(client)
    assert summary == {"expired": 0, "wave1": 0, "wave2": 0, "wave3": 0}


def test_stale_pending_expires(client, db_clean):
    sos_id = _create_aged_sos(client, age_seconds=16 * 60)
    summary = _tick(client)
    assert summary["expired"] >= 1
    status_value = _event_status(sos_id)
    assert status_value == "expired"


def test_drill_never_prompts_call_services(client, db_clean):
    sos_id = _create_aged_sos(client, age_seconds=100, drill=True)
    summary = _tick(client)
    assert summary["wave3"] == 0  # the prompt is the one thing drills skip

    victim_token = _token_for(client)
    timeline = client.get(f"/api/sos/{sos_id}/timeline", headers=auth_headers(victim_token)).json()
    assert "call_services_prompted" not in [e["event_type"] for e in timeline]


def _event_state(sos_id: str) -> tuple[int, int]:
    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        row = conn.execute(
            text("SELECT escalation_wave, radius_m FROM sos_events WHERE id = CAST(:id AS uuid)"),
            {"id": str(sos_id)},
        ).one()
        return row.escalation_wave, row.radius_m


def _event_status(sos_id: str) -> str:
    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        return conn.execute(
            text("SELECT status FROM sos_events WHERE id = CAST(:id AS uuid)"),
            {"id": str(sos_id)},
        ).scalar_one()


def _responder_notified(sos_id: str) -> bool:
    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM responses WHERE sos_event_id = CAST(:id AS uuid)"),
            {"id": str(sos_id)},
        ).scalar_one()
        return count > 0


def _token_for(client) -> str:
    # Re-login as the most recently created victim (emails embed age+drill).
    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        email = conn.execute(
            text(
                "SELECT u.email FROM users u JOIN sos_events e ON e.broadcaster_id = u.id "
                "ORDER BY e.created_at DESC LIMIT 1"
            )
        ).scalar_one()
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    return login.json()["access_token"]
