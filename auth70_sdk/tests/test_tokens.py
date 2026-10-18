import time

import pytest
from jose import jwt

from auth70_sdk import AccessTokenVerifier, SidRequired, TokenInvalid, extract_bearer

SECRET = "test-secret"
ISSUER = "http://localhost:8777"
AUDIENCE = "gates"
verifier = AccessTokenVerifier(SECRET, issuer=ISSUER, audience=AUDIENCE)


def _token(claims: dict, secret: str = SECRET) -> str:
    payload = {
        "exp": int(time.time()) + 60,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "token_use": "access",
        **claims,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_extract_bearer_absent_and_malformed():
    assert extract_bearer(None) is None
    assert extract_bearer("") is None
    assert extract_bearer("Bearer abc") == "abc"
    with pytest.raises(TokenInvalid):
        extract_bearer("Basic abc")


def test_decode_reads_subject_sid_and_scope():
    token = _token({"sub": "u1", "sid": "s1", "scope": "profile admin", "client_id": "app"})
    user = verifier.decode(token)
    assert user.sub == "u1"
    assert user.sid == "s1"
    assert user.is_admin()
    assert user.has_scope("profile")
    assert user.client_id == "app"
    assert user.iss == ISSUER
    assert user.aud == AUDIENCE
    assert user.token == token


def test_sid_and_token_use_are_required():
    with pytest.raises(SidRequired):
        verifier.decode(_token({"sub": "u1"}))
    with pytest.raises(TokenInvalid):
        verifier.decode(jwt.encode(
            {"exp": int(time.time()) + 60, "iss": ISSUER, "aud": AUDIENCE, "sub": "u1", "sid": "s1"},
            SECRET,
            algorithm="HS256",
        ))


def test_forged_and_non_access_tokens_are_rejected():
    with pytest.raises(TokenInvalid):
        verifier.decode(_token({"sub": "u1", "sid": "s1"}, secret="other"))
    machine = _token({"sub": "operator", "sid": "s1", "token_use": "client_credentials"})
    with pytest.raises(TokenInvalid):
        verifier.decode(machine)
    identity = _token({"sub": "u1", "sid": "s1", "token_use": "id"})
    with pytest.raises(TokenInvalid):
        verifier.decode(identity)


def test_wrong_audience_and_issuer_are_rejected():
    with pytest.raises(TokenInvalid):
        verifier.decode(_token({"sub": "u1", "sid": "s1", "aud": "other"}))
    with pytest.raises(TokenInvalid):
        verifier.decode(_token({"sub": "u1", "sid": "s1", "iss": "https://evil.example"}))


def test_constructor_requires_secret_issuer_and_audience():
    with pytest.raises(TokenInvalid):
        AccessTokenVerifier("  ", issuer=ISSUER, audience=AUDIENCE)
    with pytest.raises(TokenInvalid):
        AccessTokenVerifier(SECRET, issuer="", audience=AUDIENCE)
    with pytest.raises(TokenInvalid):
        AccessTokenVerifier(SECRET, issuer=ISSUER, audience="")
