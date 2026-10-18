"""Auth70 operator client: client_credentials, then session introspection and revocation."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from auth70_sdk.errors import OperatorError

SESSIONS_SCOPE = "sessions:manage"
_TOKEN_PATH = "/oauth/token"
_SESSIONS_PREFIX = "/internal/v1/sessions"


class IntrospectedSession(BaseModel):
    model_config = ConfigDict(extra="ignore")

    active: bool
    sid: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None


class _IntrospectionBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sessions: Dict[str, IntrospectedSession] = Field(default_factory=dict)


class OperatorClient:
    """Caches the operator access token and refreshes it 15 seconds before expiry."""

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        *,
        timeout: float = 5.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._base = str(base_url or "").rstrip("/")
        self._client_id = str(client_id or "").strip()
        self._client_secret = str(client_secret or "").strip()
        self._timeout = timeout
        self._http = http_client
        self._owns_http = http_client is None
        self._token = ""
        self._token_exp = 0.0
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        if self._owns_http and self._http is not None:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> "OperatorClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    def _require_config(self) -> None:
        if not self._base or not self._client_id or not self._client_secret:
            raise OperatorError("auth70 base url, client id, and client secret are required")

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self._timeout)
            self._owns_http = True
        return self._http

    async def _operator_token(self) -> str:
        self._require_config()
        async with self._lock:
            now = time.time()
            if self._token and self._token_exp - 15 > now:
                return self._token
            client = await self._client()
            try:
                response = await client.post(
                    f"{self._base}{_TOKEN_PATH}",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "scope": SESSIONS_SCOPE,
                    },
                )
                response.raise_for_status()
                body = response.json()
            except httpx.HTTPError as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                raise OperatorError("operator token request failed", status_code=status) from exc
            token = str(body.get("access_token") or "").strip() if isinstance(body, dict) else ""
            if not token:
                raise OperatorError("auth70 did not return an operator access token")
            expires_in = int(body.get("expires_in") or 120)
            self._token = token
            self._token_exp = now + max(30, expires_in)
            return token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        client = await self._client()
        try:
            response = await client.request(
                method,
                f"{self._base}{path}",
                json=payload,
                params=params,
                headers={"Authorization": f"Bearer {await self._operator_token()}"},
            )
            response.raise_for_status()
        except OperatorError:
            raise
        except httpx.HTTPError as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            raise OperatorError("auth70 session request failed", status_code=status) from exc
        if not response.content:
            return {}
        return response.json()

    async def introspect(self, sids: List[str]) -> Dict[str, IntrospectedSession]:
        unique = [sid for sid in dict.fromkeys(sids) if sid]
        if not unique:
            return {}
        body = await self._request(
            "POST",
            f"{_SESSIONS_PREFIX}/introspect",
            payload={"sids": unique},
        )
        try:
            parsed = _IntrospectionBody.model_validate(body)
        except ValidationError as exc:
            raise OperatorError("auth70 introspection response is invalid") from exc
        return parsed.sessions

    async def revoke_session(self, sid: str, *, reason: str = "service_revocation") -> Dict[str, Any]:
        if not str(sid or "").strip():
            raise OperatorError("sid is required")
        data = await self._request(
            "POST",
            f"{_SESSIONS_PREFIX}/{quote(sid, safe='')}/revoke",
            payload={"reason": reason},
        )
        return data if isinstance(data, dict) else {}

    async def revoke_user(self, user_id: str, *, reason: str = "service_revocation") -> Dict[str, Any]:
        if not str(user_id or "").strip():
            raise OperatorError("user_id is required")
        data = await self._request(
            "POST",
            f"{_SESSIONS_PREFIX}/users/{quote(user_id, safe='')}/revoke",
            payload={"reason": reason},
        )
        return data if isinstance(data, dict) else {}

    async def list_sessions(
        self,
        *,
        user_id: Optional[str] = None,
        include_inactive: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "include_inactive": include_inactive,
            "limit": limit,
        }
        if user_id:
            params["user_id"] = user_id
        data = await self._request("GET", _SESSIONS_PREFIX, params=params)
        sessions = data.get("sessions") if isinstance(data, dict) else None
        return sessions if isinstance(sessions, list) else []
