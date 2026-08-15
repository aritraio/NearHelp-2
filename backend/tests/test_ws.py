"""Integration: the real-time channel — tickets, relay, chat, broadcasts.

TestClient supports websocket_connect; both participants connect through the
same app so server-push broadcasts (create_task) land on the same loop.
"""

import uuid

from app.core.config import get_settings

from tests.conftest import auth_headers, register_user, run_sql, set_location

VICTIM = {"lat": 22.5726, "lon": 88.3639}


def _setup(client):
    victim = register_user(client, email="rt-victim@nearhelp.dev")
    responder = register_user(client, email="rt-responder@nearhelp.dev")
    stranger = register_user(client, email="rt-stranger@nearhelp.dev")
    set_location(client, victim["access_token"], VICTIM["lat"], VICTIM["lon"])
    set_location(client, responder["access_token"], VICTIM["lat"] + 0.001, VICTIM["lon"])

    sos = client.post(
        "/api/sos/create",
        headers={**auth_headers(victim["access_token"]), "Idempotency-Key": uuid.uuid4().hex},
        json={"lat": VICTIM["lat"], "lon": VICTIM["lon"], "crisis_type": "medical"},
    )
    assert sos.status_code == 201, sos.text
    return victim, responder, stranger, sos.json()["id"]


def _ticket(client, token: str, sos_id: str) -> str:
    response = client.post(f"/api/sos/{sos_id}/ws-ticket", headers=auth_headers(token))
    assert response.status_code == 200, response.text
    return response.json()["ticket"]


def test_ticket_requires_participation(client, db_clean):
    victim, responder, stranger, sos_id = _setup(client)
    assert (
        client.post(
            f"/api/sos/{sos_id}/ws-ticket", headers=auth_headers(stranger["access_token"])
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/sos/{sos_id}/ws-ticket", headers=auth_headers(victim["access_token"])
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/sos/{sos_id}/ws-ticket", headers=auth_headers(responder["access_token"])
        ).status_code
        == 200
    )


def test_ws_requires_ticket_and_it_is_single_use(client, db_clean, fake_redis):
    import pytest
    from starlette.websockets import WebSocketDisconnect

    victim, _, _, sos_id = _setup(client)

    # No ticket → the server rejects the upgrade.
    with pytest.raises(WebSocketDisconnect), client.websocket_connect(f"/api/ws/{sos_id}"):
        pass

    # Valid ticket → connect works; being inside means it was consumed.
    ticket = _ticket(client, victim["access_token"], sos_id)
    with client.websocket_connect(f"/api/ws/{sos_id}?ticket={ticket}"):
        ticket2 = _ticket(client, victim["access_token"], sos_id)
        assert ticket2 != ticket

    # The consumed ticket cannot be reused.
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(f"/api/ws/{sos_id}?ticket={ticket}"),
    ):
        pass


def test_location_relay_and_rate_limit(client, db_clean, fake_redis):
    victim, responder, _, sos_id = _setup(client)
    v_ticket = _ticket(client, victim["access_token"], sos_id)
    r_ticket = _ticket(client, responder["access_token"], sos_id)

    with (
        client.websocket_connect(f"/api/ws/{sos_id}?ticket={v_ticket}") as victim_ws,
        client.websocket_connect(f"/api/ws/{sos_id}?ticket={r_ticket}") as responder_ws,
    ):
        # Responder streams two updates inside the 2 s window; only the first relays.
        responder_ws.send_json({"type": "location_update", "lat": 22.573, "lon": 88.364})
        responder_ws.send_json({"type": "location_update", "lat": 22.574, "lon": 88.365})

        update = victim_ws.receive_json()
        assert update["type"] == "responder_update"
        assert update["responder_id"] == responder["user"]["id"]
        assert abs(update["lat"] - 22.573) < 1e-6  # first, not the rate-limited second

        # Chat: both sides see the persisted message.
        responder_ws.send_json({"type": "send_message", "text": "on my way", "language": "en"})
        # The responder also receives their own message (delivery confirmation).
        echo = responder_ws.receive_json()
        assert echo["type"] == "new_message"
        assert echo["text"] == "on my way"
        assert echo["sender_id"] == responder["user"]["id"]

        from_victim = victim_ws.receive_json()
        assert from_victim["text"] == "on my way"

    # History endpoint serves reconnects (todos.md §4 REST fallback).
    history = client.get(
        f"/api/sos/{sos_id}/messages", headers=auth_headers(victim["access_token"])
    )
    assert history.status_code == 200
    assert [m["text"] for m in history.json()] == ["on my way"]
    assert history.json()[0]["sender_name"] == "Test User"

    from sqlalchemy import text

    from tests.conftest import sync_engine

    with sync_engine.connect() as conn:
        stored = conn.execute(
            text("SELECT text FROM messages WHERE sos_event_id = CAST(:id AS uuid)"),
            {"id": str(sos_id)},
        ).scalar_one()
        assert stored == "on my way"


def test_accept_and_resolve_broadcast(client, db_clean, fake_redis):
    victim, responder, _, sos_id = _setup(client)
    v_ticket = _ticket(client, victim["access_token"], sos_id)

    with client.websocket_connect(f"/api/ws/{sos_id}?ticket={v_ticket}") as victim_ws:
        accepted = client.post(
            f"/api/sos/{sos_id}/respond", headers=auth_headers(responder["access_token"])
        )
        assert accepted.status_code == 200

        event = victim_ws.receive_json()
        assert event["type"] == "responder_accepted"
        assert event["responder_id"] == responder["user"]["id"]

        # Arrival broadcast rides the same channel.
        arrived = client.post(
            f"/api/sos/{sos_id}/arrive", headers=auth_headers(responder["access_token"])
        )
        assert arrived.status_code == 200
        assert arrived.json()["status"] == "arrived"

        event = victim_ws.receive_json()
        assert event["type"] == "responder_arrived"

        resolved = client.put(
            f"/api/sos/{sos_id}/resolve", headers=auth_headers(victim["access_token"]), json={}
        )
        assert resolved.status_code == 200
        event = victim_ws.receive_json()
        assert event["type"] == "sos_resolved"


def test_escalation_broadcasts_on_channel(client, db_clean, fake_redis):
    victim, responder, _, sos_id = _setup(client)
    v_ticket = _ticket(client, victim["access_token"], sos_id)

    with client.websocket_connect(f"/api/ws/{sos_id}?ticket={v_ticket}") as victim_ws:
        run_sql(
            "UPDATE sos_events SET created_at = now() - interval '100 seconds' "
            "WHERE id = CAST(:id AS uuid)",
            {"id": str(sos_id)},
        )
        tick = client.post(
            "/internal/escalation/tick",
            headers={"X-Tick-Secret": get_settings().internal_tick_secret},
        )
        assert tick.status_code == 200

        for _ in range(3):  # wave1, wave2, call_services_prompt
            message = victim_ws.receive_json()
            assert message["type"] in {"escalation_wave", "call_services_prompt"}
            if message["type"] == "escalation_wave":
                assert message["radius_m"] in {4000, 12000}
