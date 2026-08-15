"""Unit tests for the security core — no database required."""

import time
import uuid

import jwt
import pytest
from app.core.config import get_settings
from app.core.security import (
    PasswordTooLong,
    create_token_pair,
    decode_token,
    hash_password,
    refresh_expiry_seconds,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong", hashed)


def test_bcrypt_cost_factor_12():
    assert hash_password("s3cret-pass").startswith("$2b$12$")


def test_password_over_72_bytes_rejected():
    with pytest.raises(PasswordTooLong):
        hash_password("long-password" * 8)  # 104 bytes


def test_malformed_hash_rejected_not_raised():
    assert not verify_password("x", "not-a-bcrypt-hash")


def test_token_pair_roundtrip():
    user_id = uuid.uuid4()
    pair = create_token_pair(user_id)

    access = decode_token(pair["access_token"], expected_type="access")
    assert access["sub"] == str(user_id)
    assert access["type"] == "access"

    refresh = decode_token(pair["refresh_token"], expected_type="refresh")
    assert refresh["sub"] == str(user_id)
    assert refresh["jti"]


def test_access_token_ttl_is_15_minutes():
    settings = get_settings()
    pair = create_token_pair(uuid.uuid4())
    access = decode_token(pair["access_token"], expected_type="access")
    assert access["exp"] - access["iat"] == settings.access_token_ttl_min * 60


def test_token_type_confusion_rejected():
    pair = create_token_pair(uuid.uuid4())
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(pair["access_token"], expected_type="refresh")


def test_tampered_token_rejected():
    token = create_token_pair(uuid.uuid4())["access_token"]
    with pytest.raises(jwt.PyJWTError):
        decode_token(token + "x", expected_type="access")


def test_wrong_secret_rejected():
    token = create_token_pair(uuid.uuid4())["access_token"]
    settings = get_settings()
    original = settings.jwt_secret
    settings.jwt_secret = "other-secret"
    try:
        with pytest.raises(jwt.PyJWTError):
            decode_token(token, expected_type="access")
    finally:
        settings.jwt_secret = original


def test_refresh_expiry_math():
    payload = {"exp": int(time.time()) + 30}
    assert 29 <= refresh_expiry_seconds(payload) <= 30
    assert refresh_expiry_seconds({"exp": int(time.time()) - 5}) == 0
