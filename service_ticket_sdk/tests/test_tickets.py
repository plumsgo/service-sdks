import time

import pytest
from jose import jwt

from service_ticket_sdk import (
    ActingInvalid,
    ActingPrincipal,
    AudienceMismatch,
    IssuerNotAllowed,
    IssuerSubjectMismatch,
    MAX_TTL_SECONDS,
    TOKEN_USE,
    SecretNotConfigured,
    ServiceTickets,
    TokenExpired,
    TokenInvalid,
    TokenUseInvalid,
    TtlInvalid,
    extract_bearer,
    mint_service_token,
    verify_service_token,
)

SECRET = "test-service-secret"
ISSUER = "billing"


def _mint(**kwargs):
    return mint_service_token(
        secret=SECRET,
        issuer=ISSUER,
        audience="ledger:internal",
        **kwargs,
    )


def _verify(token, **kwargs):
    return verify_service_token(
        token,
        secret=SECRET,
        expected_audience="ledger:internal",
        allowed_issuers={ISSUER, "bff"},
        **kwargs,
    )


def _raw(**claims):
    payload = {
        "token_use": TOKEN_USE,
        "iss": ISSUER,
        "sub": ISSUER,
        "aud": "ledger:internal",
        "exp": int(time.time()) + 60,
        **claims,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_extract_bearer_absent_and_malformed():
    assert extract_bearer(None) is None
    assert extract_bearer("") is None
    assert extract_bearer("Bearer abc") == "abc"
    with pytest.raises(TokenInvalid):
        extract_bearer("Basic abc")


def test_round_trip_with_acting_and_scope():
    token = _mint(
        acting=ActingPrincipal(kind="user", subject_id="u1", auth_session_id="s1"),
        scopes=("ledger:write", "ledger:read"),
    )
    identity = _verify(token)
    assert identity.issuer == ISSUER
    assert identity.subject == ISSUER
    assert identity.audience == "ledger:internal"
    assert identity.acting is not None
    assert identity.acting.kind == "user"
    assert identity.acting.subject_id == "u1"
    assert identity.acting.auth_session_id == "s1"
    assert identity.has_scope("ledger:write")
    assert not identity.has_scope("admin")
    assert jwt.get_unverified_claims(token)["token_use"] == TOKEN_USE


def test_forged_expired_and_wrong_audience_raise():
    token = _mint()
    with pytest.raises(TokenInvalid):
        verify_service_token(
            token,
            secret="other",
            expected_audience="ledger:internal",
            allowed_issuers={ISSUER},
        )
    with pytest.raises(AudienceMismatch):
        verify_service_token(
            token,
            secret=SECRET,
            expected_audience="other:internal",
            allowed_issuers={ISSUER},
        )
    expired = _raw(exp=int(time.time()) - 10)
    with pytest.raises(TokenExpired):
        _verify(expired)


def test_issuer_must_equal_subject_and_be_allowlisted():
    with pytest.raises(IssuerSubjectMismatch):
        _verify(_raw(sub="not-billing"))
    with pytest.raises(IssuerNotAllowed) as exc:
        verify_service_token(
            _mint(),
            secret=SECRET,
            expected_audience="ledger:internal",
            allowed_issuers={"room"},
        )
    assert exc.value.http_status == 403
    assert exc.value.code == "issuer_not_allowed"


def test_omitting_allowlist_accepts_any_issuer():
    identity = verify_service_token(
        _mint(),
        secret=SECRET,
        expected_audience="ledger:internal",
    )
    assert identity.issuer == ISSUER
    with pytest.raises(IssuerNotAllowed):
        verify_service_token(
            _mint(),
            secret=SECRET,
            expected_audience="ledger:internal",
            allowed_issuers=(),
        )


def test_unknown_or_incomplete_acting_is_rejected():
    with pytest.raises(ActingInvalid):
        _verify(_raw(acting_kind="robot", acting_subject="u9"))
    with pytest.raises(ActingInvalid):
        _verify(_raw(acting_subject="u9"))
    with pytest.raises(ActingInvalid):
        _verify(_raw(acting_kind="user"))
    with pytest.raises(ActingInvalid):
        _verify(_raw(acting_sid="s1"))


def test_user_access_token_shape_is_rejected():
    user = jwt.encode(
        {
            "iss": "auth70",
            "sub": "u1",
            "aud": "ledger:internal",
            "exp": int(time.time()) + 60,
        },
        SECRET,
        algorithm="HS256",
    )
    with pytest.raises(TokenUseInvalid):
        _verify(user)


def test_ttl_is_capped():
    with pytest.raises(TtlInvalid):
        _mint(ttl_seconds=MAX_TTL_SECONDS + 1)
    with pytest.raises(TtlInvalid):
        _mint(ttl_seconds=0)
    with pytest.raises(TtlInvalid):
        ServiceTickets(SECRET, ISSUER, ttl_seconds=MAX_TTL_SECONDS + 1)
    token = _mint(ttl_seconds=MAX_TTL_SECONDS)
    assert _verify(token).issuer == ISSUER


def test_service_tickets_helper_binds_issuer():
    tickets = ServiceTickets(SECRET, ISSUER)
    token = tickets.mint("ledger:internal", acting=ActingPrincipal(subject_id="u2"))
    identity = tickets.verify(
        token,
        expected_audience="ledger:internal",
        allowed_issuers={tickets.issuer},
    )
    assert identity.acting is not None
    assert identity.acting.subject_id == "u2"


def test_mint_rejects_empty_secret_or_issuer():
    with pytest.raises(SecretNotConfigured):
        mint_service_token(secret="  ", issuer=ISSUER, audience="ledger:internal")
    with pytest.raises(TokenInvalid):
        mint_service_token(secret=SECRET, issuer="", audience="ledger:internal")
    with pytest.raises(SecretNotConfigured):
        ServiceTickets("  ", ISSUER)
