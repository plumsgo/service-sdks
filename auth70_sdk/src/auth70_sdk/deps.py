"""FastAPI dependencies for resource servers that accept Auth70 user access tokens.

Install with the fastapi extra. This module checks the bearer token only.
It does not forward that token to another service.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request

from auth70_sdk.errors import Auth70Error, SidRequired
from auth70_sdk.tokens import AccessToken, AccessTokenVerifier, extract_bearer


class AccessTokenDeps:
    def __init__(self, verifier: AccessTokenVerifier) -> None:
        self.verifier = verifier

    async def require_user(self, request: Request) -> AccessToken:
        header = request.headers.get("authorization")
        try:
            token = extract_bearer(header)
        except Auth70Error as exc:
            raise HTTPException(status_code=401, detail="invalid_authorization") from exc
        if not token:
            raise HTTPException(status_code=401, detail="missing_token")
        try:
            return self.verifier.decode(token)
        except SidRequired as exc:
            raise HTTPException(status_code=401, detail="missing_sid") from exc
        except Auth70Error as exc:
            raise HTTPException(status_code=401, detail="invalid_token") from exc

    async def optional_user(self, request: Request) -> Optional[AccessToken]:
        try:
            return await self.require_user(request)
        except HTTPException:
            return None

    async def require_admin(self, request: Request) -> AccessToken:
        user = await self.require_user(request)
        if not user.is_admin():
            raise HTTPException(status_code=403, detail="admin_required")
        return user
