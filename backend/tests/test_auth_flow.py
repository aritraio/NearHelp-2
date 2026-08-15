"""Integration: auth lifecycle — register → login → me → refresh rotation.

Requires Postgres (skips automatically when the stack is not running).
"""

from tests.conftest import auth_headers, register_user


def test_register_login_me_roundtrip(client, db_clean):
    tokens = register_user(client, email="amit@nearhelp.dev")
    assert tokens["token_type"] == "bearer"
    assert tokens["user"]["email"] == "amit@nearhelp.dev"
    assert tokens["user"]["trust_score"] == 50.0

    login = client.post(
        "/api/auth/login", json={"email": "amit@nearhelp.dev", "password": "secret123"}
    )
    assert login.status_code == 200
    body = login.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["id"] == tokens["user"]["id"]

    me = client.get("/api/users/me", headers=auth_headers(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "amit@nearhelp.dev"


def test_duplicate_email_rejected(client, db_clean):
    register_user(client, email="dup@nearhelp.dev")
    again = client.post(
        "/api/auth/register",
        json={"email": "DUP@nearhelp.dev", "password": "secret123", "name": "Dup"},
    )
    assert again.status_code == 409


def test_login_wrong_password_same_error_as_unknown_email(client, db_clean):
    register_user(client, email="real@nearhelp.dev")
    wrong_pw = client.post(
        "/api/auth/login", json={"email": "real@nearhelp.dev", "password": "nope-nope"}
    )
    unknown = client.post(
        "/api/auth/login", json={"email": "ghost@nearhelp.dev", "password": "nope-nope"}
    )
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json()["detail"] == unknown.json()["detail"]


def test_short_password_rejected_without_touching_db(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "x@y.dev", "password": "short", "name": "X"},
    )
    assert response.status_code == 422


def test_me_requires_token(client):
    assert client.get("/api/users/me").status_code == 401
    assert (
        client.get("/api/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    )


def test_refresh_rotation_and_replay_rejected(client, db_clean, fake_redis):
    tokens = register_user(client, email="rot@nearhelp.dev")
    old_refresh = tokens["refresh_token"]

    rotated = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != old_refresh

    # Replaying the burned token must fail — this is the rotation guarantee.
    replay = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401

    # And the new token still works.
    again = client.post(
        "/api/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}
    )
    assert again.status_code == 200


def test_refresh_rejects_access_token(client, db_clean):
    tokens = register_user(client, email="type@nearhelp.dev")
    response = client.post("/api/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401
