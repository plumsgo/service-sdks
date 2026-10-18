"""FastAPI dependencies for a gate that accepts user tokens or service tickets.

Install with the fastapi extra. This module does not forward the inbound token.
"""
from __future__ import annotations

from fastapi import HTTPException, Request

from auth70_sdk.errors import Auth70Error
from service_ticket_sdk import ServiceTicketError

from gate_auth_sdk.auth import GateAuth
from gate_auth_sdk.errors import GateAuthError
from gate_auth_sdk.principal import Principal


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, GateAuthError):
        return HTTPException(status_code=exc.http_status, detail=exc.code)
    if isinstance(exc, ServiceTicketError):
        return HTTPException(status_code=exc.http_status, detail=exc.code)
    if isinstance(exc, Auth70Error):
        return HTTPException(status_code=401, detail="invalid_token")
    raise exc


class GateAuthDeps:
    def __init__(self, auth: GateAuth) -> None:
        self.auth = auth

    async def require_principal(self, request: Request) -> Principal:
        try:
            return self.auth.authenticate(request.headers.get("authorization"))
        except (GateAuthError, ServiceTicketError, Auth70Error) as exc:
            raise _http_error(exc) from exc

    async def require_user(self, request: Request) -> Principal:
        try:
            return self.auth.require_user(request.headers.get("authorization"))
        except (GateAuthError, ServiceTicketError, Auth70Error) as exc:
            raise _http_error(exc) from exc

    async def require_admin(self, request: Request) -> Principal:
        try:
            return self.auth.require_admin(request.headers.get("authorization"))
        except (GateAuthError, ServiceTicketError, Auth70Error) as exc:
            raise _http_error(exc) from exc
