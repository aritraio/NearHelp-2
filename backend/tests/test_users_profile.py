"""Integration: profile updates, multi-device FCM tokens, skill claims."""

from tests.conftest import auth_headers, register_user

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fakemachine" * 8  # ~88 bytes of fake PNG


def _setup(client, email="priya@nearhelp.dev"):
    tokens = register_user(client, email=email)
    return auth_headers(tokens["access_token"]), tokens


def test_update_profile_fields(client, db_clean):
    headers, _ = _setup(client)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json={"name": "Priya Sharma", "languages": ["bn", "en"], "phone": "+919812345678"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Priya Sharma"
    assert body["languages"] == ["bn", "en"]

    me = client.get("/api/users/me", headers=headers)
    assert me.json()["phone"] == "+919812345678"


def test_invalid_language_code_rejected(client, db_clean):
    headers, _ = _setup(client)
    response = client.put("/api/users/me", headers=headers, json={"languages": ["bengali"]})
    assert response.status_code == 422


def test_fcm_token_multi_device(client, db_clean):
    headers, _ = _setup(client)
    # Two devices register independently.
    assert (
        client.post(
            "/api/users/me/fcm-token",
            headers=headers,
            json={"device_id": "device-aaa-111", "fcm_token": "fcm-token-first-device-0001"},
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/users/me/fcm-token",
            headers=headers,
            json={"device_id": "device-bbb-222", "fcm_token": "fcm-token-second-0002"},
        ).status_code
        == 204
    )
    # Rotating one device's token must not disturb the other.
    assert (
        client.post(
            "/api/users/me/fcm-token",
            headers=headers,
            json={"device_id": "device-aaa-111", "fcm_token": "fcm-token-rotated-0003"},
        ).status_code
        == 204
    )


def test_skill_claim_with_certificate(client, db_clean):
    headers, _ = _setup(client)
    claim = client.post(
        "/api/users/me/skills",
        headers=headers,
        params={"skill_type": "cpr_certified"},
        files={"certificate": ("cpr.png", PNG_BYTES, "image/png")},
    )
    assert claim.status_code == 201, claim.text
    body = claim.json()
    assert body["skill_type"] == "cpr_certified"
    assert body["status"] == "pending"
    assert body["has_certificate"] is True

    listed = client.get("/api/users/me/skills", headers=headers).json()
    assert [row["skill_type"] for row in listed] == ["cpr_certified"]

    download = client.get(f"/api/users/me/skills/{body['id']}/certificate", headers=headers)
    assert download.status_code == 200
    assert download.content == PNG_BYTES
    assert download.headers["content-type"] == "image/png"


def test_skill_claim_without_certificate(client, db_clean):
    headers, _ = _setup(client)
    claim = client.post(
        "/api/users/me/skills", headers=headers, params={"skill_type": "first_aid_trained"}
    )
    assert claim.status_code == 201
    assert claim.json()["has_certificate"] is False
    missing = client.get(f"/api/users/me/skills/{claim.json()['id']}/certificate", headers=headers)
    assert missing.status_code == 404


def test_unknown_skill_rejected(client, db_clean):
    headers, _ = _setup(client)
    response = client.post("/api/users/me/skills", headers=headers, params={"skill_type": "wizard"})
    assert response.status_code == 422


def test_certificate_wrong_type_rejected(client, db_clean):
    headers, _ = _setup(client)
    response = client.post(
        "/api/users/me/skills",
        headers=headers,
        params={"skill_type": "nurse"},
        files={"certificate": ("notes.exe", b"MZ...", "application/octet-stream")},
    )
    assert response.status_code == 415


def test_cannot_download_anothers_certificate(client, db_clean):
    owner_headers, owner = _setup(client, email="owner@nearhelp.dev")
    claim = client.post(
        "/api/users/me/skills",
        headers=owner_headers,
        params={"skill_type": "doctor"},
        files={"certificate": ("degree.png", PNG_BYTES, "image/png")},
    ).json()

    other_tokens = register_user(client, email="other@nearhelp.dev")
    other_headers = auth_headers(other_tokens["access_token"])
    response = client.get(f"/api/users/me/skills/{claim['id']}/certificate", headers=other_headers)
    assert response.status_code == 404  # invisible, not 403 — no existence leak
