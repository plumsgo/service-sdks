import time

import pytest
from jose import jwt

from auth70_sdk.errors import TokenInvalid
from service_ticket_sdk import ActingPrincipal, IssuerNotAllowed, ServiceTickets

from gate_auth_sdk import (
    ActingRequired,
    AdminRequired,
    GateAuth,
    MissingToken,
    TokenUseInvalid,
    parse_issuers,
)

USER_SECRET = "user-secret"
SERVICE_SECRET = "service-secret"
ISSUER = "figure-gate"
AUDIENCE = "figure-gate:internal"
USER_ISSUER = "http://localhost:8777"
USER_AUDIENCE = "gates"


def _user_token(**claims) -> str:
    payload = {
        "exp": int(time.time()) + 60,
        "iss": USER_ISSUER,
        "aud": USER_AUDIENCE,
        "token_use": "access",
        "sub": "u1",
        "sid": "s1",
        **claims,
    }
    return jwt.encode(payload, USER_SECRET, algorithm="HS256")


def _gate(**kwargs) -> GateAuth:
    options = {
        "issuer": ISSUER,
        "audience": AUDIENCE,
        "user_secret": USER_SECRET,
        "service_secret": SERVICE_SECRET,
        "user_issuer": USER_ISSUER,
        "user_audience": USER_AUDIENCE,
        "allowed_issuers": {"board"},
    }
    options.update(kwargs)
    return GateAuth(**options)


def _service_token(*, issuer: str = "board", **kwargs) -> str:
    return ServiceTickets(SERVICE_SECRET, issuer).mint(AUDIENCE, **kwargs)


def test_parse_issuers_from_env_and_empty():
    assert parse_issuers("board, chat") == frozenset({"board", "chat"})
    assert parse_issuers("") == frozenset()
    assert parse_issuers(None) == frozenset()
    assert parse_issuers(["board", " board "]) == frozenset({"board"})


def test_user_token_becomes_principal():
    principal = _gate().authenticate(f"Bearer {_user_token(scope='admin')}")
    assert principal.sub == "u1"
    assert principal.sid == "s1"
    assert principal.admin
    assert principal.via == "user"
    assert principal.caller == "user"
    assert principal.is_admin()


def test_id_token_is_rejected():
    token = _user_token(token_use="id")
    with pytest.raises(TokenUseInvalid):
        _gate().authenticate(f"Bearer {token}")


def test_service_ticket_with_acting():
    token = _service_token(
        acting=ActingPrincipal(kind="user", subject_id="u2", auth_session_id="s2"),
        scopes=("admin",),
    )
    principal = _gate().authenticate(f"Bearer {token}")
    assert principal.sub == "u2"
    assert principal.sid == "s2"
    assert principal.admin
    assert principal.via == "service"
    assert principal.caller == "board"


def test_admin_machine_ticket_has_no_acting():
    principal = _gate().authenticate(f"Bearer {_service_token(scopes=('admin',))}")
    assert principal.sub is None
    assert principal.admin
    with pytest.raises(ActingRequired):
        _gate().require_user(f"Bearer {_service_token(scopes=('admin',))}")


def test_require_admin_rejects_plain_user():
    with pytest.raises(AdminRequired):
        _gate().require_admin(f"Bearer {_user_token()}")


def test_missing_and_forged_user_tokens():
    with pytest.raises(MissingToken):
        _gate().authenticate(None)
    forged = jwt.encode(
        {
            "exp": int(time.time()) + 60,
            "iss": USER_ISSUER,
            "aud": USER_AUDIENCE,
            "token_use": "access",
            "sub": "u1",
            "sid": "s1",
        },
        "other",
        algorithm="HS256",
    )
    with pytest.raises(TokenInvalid):
        _gate().authenticate(f"Bearer {forged}")


def test_unknown_service_issuer_is_rejected():
    token = _service_token(issuer="stranger")
    with pytest.raises(IssuerNotAllowed):
        _gate().authenticate(f"Bearer {token}")


def test_empty_allow_list_rejects_all_service_callers():
    token = _service_token()
    with pytest.raises(IssuerNotAllowed):
        _gate(allowed_issuers=frozenset()).authenticate(f"Bearer {token}")


def test_unrestricted_issuers_accept_any_caller():
    token = ServiceTickets(SERVICE_SECRET, "anyone").mint(AUDIENCE)
    principal = _gate(allowed_issuers=None).authenticate(f"Bearer {token}")
    assert principal.caller == "anyone"


def test_remint_copies_acting_and_admin_scope():
    principal = _gate().authenticate(f"Bearer {_user_token(scope='admin')}")
    outbound = _gate().ticket_for(principal, "figures:internal")
    identity = ServiceTickets(SERVICE_SECRET, ISSUER).verify(
        outbound,
        expected_audience="figures:internal",
        allowed_issuers={ISSUER},
    )
    assert identity.issuer == ISSUER
    assert identity.has_scope("admin")
    assert identity.acting is not None
    assert identity.acting.subject_id == "u1"
    assert identity.acting.auth_session_id == "s1"


def test_remint_machine_admin_has_no_acting():
    principal = _gate().require_admin(f"Bearer {_service_token(scopes=('admin',))}")
    outbound = _gate().ticket_for(principal, "storage:internal")
    identity = ServiceTickets(SERVICE_SECRET, ISSUER).verify(
        outbound,
        expected_audience="storage:internal",
        allowed_issuers={ISSUER},
    )
    assert identity.acting is None
    assert identity.has_scope("admin")
