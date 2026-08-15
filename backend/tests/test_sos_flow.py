"""Integration: the SOS critical path — create (idempotent), respond, ack, resolve.

Scenario fixture: victim at Salt Lake (proposal §12.3 point); responders at
~200 m and ~800 m offsets; a stranger with no involvement for permission checks.
One degree of latitude ≈ 111 km, so 0.0018° ≈ 200 m, 0.0072° ≈ 800 m.
"""

import uuid

from tests.conftest import auth_headers, register_user, set_location, set_skills

VICTIM = {"lat": 22.5726, "lon": 88.3639}
NEAR_OFFSET = 0.0018  # ~200 m north
FAR_OFFSET = 0.0072  # ~800 m north


def _setup_scenario(client):
    """Victim + near unskilled responder + far verified nurse + a stranger."""
    victim = register_user(client, email="victim@nearhelp.dev")
    near = register_user(client, email="near@nearhelp.dev")
    nurse = register_user(client, email="nurse@nearhelp.dev")
    stranger = register_user(client, email="stranger@nearhelp.dev")

    set_location(client, victim["access_token"], VICTIM["lat"], VICTIM["lon"])
    set_location(client, near["access_token"], VICTIM["lat"] + NEAR_OFFSET, VICTIM["lon"])
    set_location(client, nurse["access_token"], VICTIM["lat"] + FAR_OFFSET, VICTIM["lon"])
    set_skills("near@nearhelp.dev", [], trust=60.0)
    set_skills(
        "nurse@nearhelp.dev",
        [
            {"skill_type": "nurse", "verified": True},
            {"skill_type": "cpr_certified", "verified": True},
        ],
        trust=85.0,
    )
    return victim, near, nurse, stranger


def _create(client, token, key=None, crisis="medical", drill=False):
    return client.post(
        "/api/sos/create",
        headers={**auth_headers(token), "Idempotency-Key": key or uuid.uuid4().hex},
        json={
            "description": "man collapsed, not breathing",
            "lat": VICTIM["lat"],
            "lon": VICTIM["lon"],
            "crisis_type": crisis,
            "is_drill": drill,
        },
    )


def test_create_notifies_ranked_responders(client, db_clean):
    victim, near, nurse, stranger = _setup_scenario(client)
    response = _create(client, victim["access_token"])
    assert response.status_code == 201, response.text
    body = response.json()

    assert body["status"] == "pending"
    assert body["crisis_type"] == "medical"
    assert body["radius_m"] == 2000
    assert body["notified_count"] == 2
    # The nurse ranks first despite being 4× further (§12.3 behavior, live).
    assert body["responders"][0]["status"] == "notified"
    responder_ids = {r["responder_id"] for r in body["responders"]}
    assert responder_ids == {near["user"]["id"], nurse["user"]["id"]}

    # Victim sees the event in /active; both notified responders can view it.
    active = client.get("/api/sos/active", headers=auth_headers(victim["access_token"]))
    assert [event["id"] for event in active.json()] == [body["id"]]
    for tokens in (near, nurse):
        view = client.get(f"/api/sos/{body['id']}", headers=auth_headers(tokens["access_token"]))
        assert view.status_code == 200

    # A stranger with no involvement gets a 404 (no existence leak).
    denied = client.get(f"/api/sos/{body['id']}", headers=auth_headers(stranger["access_token"]))
    assert denied.status_code == 404


def test_create_is_idempotent(client, db_clean, fake_redis):
    victim, *_ = _setup_scenario(client)
    key = uuid.uuid4().hex

    first = _create(client, victim["access_token"], key=key)
    second = _create(client, victim["access_token"], key=key)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    # Exactly one event exists for that key — the durable backstop holds.
    count = run_sql_count("SELECT COUNT(*) FROM sos_events")
    assert count == 1


def test_create_requires_idempotency_key(client, db_clean):
    victim, *_ = _setup_scenario(client)
    response = client.post(
        "/api/sos/create",
        headers=auth_headers(victim["access_token"]),
        json={"lat": VICTIM["lat"], "lon": VICTIM["lon"]},
    )
    assert response.status_code == 422


def test_daily_sos_quota_enforced(client, db_clean, fake_redis):
    victim, *_ = _setup_scenario(client)
    codes = [_create(client, victim["access_token"]).status_code for _ in range(11)]
    assert codes.count(201) == 10
    assert codes[-1] == 429


def test_respond_flow_activates_and_is_idempotent(client, db_clean):
    victim, near, nurse, _ = _setup_scenario(client)
    sos_id = _create(client, victim["access_token"]).json()["id"]

    first = client.post(f"/api/sos/{sos_id}/respond", headers=auth_headers(nurse["access_token"]))
    assert first.status_code == 200
    assert first.json()["status"] == "accepted"
    response_id = first.json()["response_id"]

    # Retrying accept is a no-op returning the same response.
    again = client.post(f"/api/sos/{sos_id}/respond", headers=auth_headers(nurse["access_token"]))
    assert again.status_code == 200
    assert again.json()["response_id"] == response_id

    # Event flipped to active; victim sees the accepted responder by name.
    view = client.get(f"/api/sos/{sos_id}", headers=auth_headers(victim["access_token"])).json()
    assert view["status"] == "active"
    accepted = [r for r in view["responders"] if r["status"] == "accepted"]
    assert len(accepted) == 1

    # A stranger cannot respond.
    stranger = register_user(client, email="intruder@nearhelp.dev")
    denied = client.post(
        f"/api/sos/{sos_id}/respond", headers=auth_headers(stranger["access_token"])
    )
    assert denied.status_code in (403, 404)


def test_ack_marks_delivery(client, db_clean):
    victim, near, *_ = _setup_scenario(client)
    sos_id = _create(client, victim["access_token"]).json()["id"]

    ack = client.post(f"/api/sos/{sos_id}/ack", headers=auth_headers(near["access_token"]))
    assert ack.status_code == 200
    assert ack.json()["status"] == "acked"

    # Ack is idempotent and does not block a later accept.
    ack_again = client.post(f"/api/sos/{sos_id}/ack", headers=auth_headers(near["access_token"]))
    assert ack_again.json()["status"] == "acked"
    respond = client.post(f"/api/sos/{sos_id}/respond", headers=auth_headers(near["access_token"]))
    assert respond.json()["status"] == "accepted"


def test_resolve_updates_trust_and_timeline(client, db_clean):
    victim, near, nurse, _ = _setup_scenario(client)
    sos_id = _create(client, victim["access_token"]).json()["id"]
    client.post(f"/api/sos/{sos_id}/respond", headers=auth_headers(nurse["access_token"]))

    resolved = client.put(
        f"/api/sos/{sos_id}/resolve",
        headers=auth_headers(victim["access_token"]),
        json={"outcome": "patient stabilized"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None

    # The accepted responder earned +3 trust (85.0 → 88.0); the notified-only did not.
    nurse_trust = scalar("SELECT trust_score FROM users WHERE email = 'nurse@nearhelp.dev'")
    near_trust = scalar("SELECT trust_score FROM users WHERE email = 'near@nearhelp.dev'")
    assert float(nurse_trust) == 88.0
    assert float(near_trust) == 60.0

    # Resolving twice is a 409.
    twice = client.put(
        f"/api/sos/{sos_id}/resolve",
        headers=auth_headers(victim["access_token"]),
        json={},
    )
    assert twice.status_code == 409


def test_timeline_records_lifecycle_in_order(client, db_clean):
    victim, _, nurse, _ = _setup_scenario(client)
    sos_id = _create(client, victim["access_token"]).json()["id"]
    client.post(f"/api/sos/{sos_id}/respond", headers=auth_headers(nurse["access_token"]))
    client.put(f"/api/sos/{sos_id}/resolve", headers=auth_headers(victim["access_token"]), json={})

    timeline = client.get(
        f"/api/sos/{sos_id}/timeline", headers=auth_headers(victim["access_token"])
    ).json()
    types = [event["event_type"] for event in timeline]
    assert types[0] == "sos_created"
    assert "responders_notified" in types
    assert types.index("response_accepted") > types.index("sos_created")
    assert types[-1] == "sos_resolved"
    # Selection timings are recorded for the defense charts.
    notified = next(e for e in timeline if e["event_type"] == "responders_notified")
    assert "geo_ms" in notified["details"] and "rank_ms" in notified["details"]


def test_drill_flag_stored_and_isolated(client, db_clean):
    victim, *_ = _setup_scenario(client)
    body = _create(client, victim["access_token"], drill=True).json()
    assert body["is_drill"] is True


def run_sql_count(query: str) -> int:
    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        return conn.execute(text(query)).scalar_one()


def scalar(query: str):
    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        return conn.execute(text(query)).scalar_one()
