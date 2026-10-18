import time

import pytest
from fastapi import HTTPException
from jose import jwt
from starlette.requests import Request

from auth70_sdk import AccessTokenVerifier
from auth70_sdk.deps import AccessTokenDeps

SECRET = "test-secret"
ISSUER = "http://localhost:8777"
AUDIENCE = "gates"
deps = AccessTokenDeps(AccessTokenVerifier(SECRET, issuer=ISSUER, audience=AUDIENCE))


def _request(authorization: str | None) -> Request:
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers})


def _token(**claims) -> str:
    payload = {
        "exp": int(time.time()) + 60,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "token_use": "access",
        "sub": "u1",
        "sid": "s1",
        **claims,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


@pytest.mark.asyncio
async def test_require_user_and_admin():
    user = await deps.require_user(_request(f"Bearer {_token(scope='admin')}"))
    assert user.sub == "u1"
    admin = await deps.require_admin(_request(f"Bearer {_token(scope='admin')}"))
    assert admin.is_admin()
    with pytest.raises(HTTPException) as missing:
        await deps.require_user(_request(None))
    assert missing.value.detail == "missing_token"
    with pytest.raises(HTTPException) as no_sid:
        await deps.require_user(_request(f"Bearer {_token(sid='')}"))
    assert no_sid.value.detail == "missing_sid"
    with pytest.raises(HTTPException) as forbidden:
        await deps.require_admin(_request(f"Bearer {_token()}"))
    assert forbidden.value.status_code == 403


@pytest.mark.asyncio
async def test_optional_user_swallows_auth_failures():
    assert await deps.optional_user(_request(None)) is None
    assert await deps.optional_user(_request("Bearer not-a-jwt")) is None
