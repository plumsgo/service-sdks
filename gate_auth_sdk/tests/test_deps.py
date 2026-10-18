import time

import pytest
from fastapi import HTTPException
from jose import jwt
from starlette.requests import Request

from service_ticket_sdk import ActingPrincipal, ServiceTickets

from gate_auth_sdk import GateAuth
from gate_auth_sdk.deps import GateAuthDeps

USER_SECRET = "user-secret"
SERVICE_SECRET = "service-secret"
USER_ISSUER = "http://localhost:8777"
USER_AUDIENCE = "gates"
deps = GateAuthDeps(
    GateAuth(
        issuer="figure-gate",
        audience="figure-gate:internal",
        user_secret=USER_SECRET,
        service_secret=SERVICE_SECRET,
        user_issuer=USER_ISSUER,
        user_audience=USER_AUDIENCE,
        allowed_issuers={"board"},
    )
)


def _request(authorization: str | None) -> Request:
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers})


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


@pytest.mark.asyncio
async def test_require_user_and_admin_from_user_token():
    user = await deps.require_user(_request(f"Bearer {_user_token(scope='admin')}"))
    assert user.sub == "u1"
    admin = await deps.require_admin(_request(f"Bearer {_user_token(scope='admin')}"))
    assert admin.is_admin()
    with pytest.raises(HTTPException) as missing:
        await deps.require_user(_request(None))
    assert missing.value.detail == "missing_token"
    with pytest.raises(HTTPException) as forbidden:
        await deps.require_admin(_request(f"Bearer {_user_token()}"))
    assert forbidden.value.status_code == 403
    assert forbidden.value.detail == "admin_required"


@pytest.mark.asyncio
async def test_service_ticket_maps_issuer_errors():
    token = ServiceTickets(SERVICE_SECRET, "stranger").mint("figure-gate:internal")
    with pytest.raises(HTTPException) as denied:
        await deps.require_principal(_request(f"Bearer {token}"))
    assert denied.value.status_code == 403
    assert denied.value.detail == "issuer_not_allowed"


@pytest.mark.asyncio
async def test_machine_admin_allowed_without_acting():
    token = ServiceTickets(SERVICE_SECRET, "board").mint(
        "figure-gate:internal",
        scopes=("admin",),
    )
    principal = await deps.require_admin(_request(f"Bearer {token}"))
    assert principal.sub is None
    with pytest.raises(HTTPException) as acting:
        await deps.require_user(_request(f"Bearer {token}"))
    assert acting.value.detail == "acting_required"


@pytest.mark.asyncio
async def test_service_ticket_with_acting_is_a_user():
    token = ServiceTickets(SERVICE_SECRET, "board").mint(
        "figure-gate:internal",
        acting=ActingPrincipal(kind="user", subject_id="u9", auth_session_id="s9"),
    )
    user = await deps.require_user(_request(f"Bearer {token}"))
    assert user.sub == "u9"
    assert user.via == "service"
