"""Verify Auth70 user access tokens.

Accepts only ``token_use=access`` with ``sid``, ``iss``, and ``aud``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from jose import JWTError, jwt

from auth70_sdk.errors import SidRequired, TokenInvalid

TOKEN_USE = "access"


def extract_bearer(authorization: Optional[str]) -> Optional[str]:
    """Return the bearer token, or None when the header is absent.

    A present but malformed Authorization header raises TokenInvalid.
    """
    raw = (authorization or "").strip()
    if not raw:
        return None
    scheme, _, token = raw.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise TokenInvalid("invalid_authorization")
    return token.strip()


@dataclass(frozen=True)
class AccessToken:
    """Verified user access token. ``token`` is the original string."""

    sub: str
    sid: str
    token: str = field(repr=False)
    scope: str = ""
    client_id: str = ""
    iss: str = ""
    aud: str = ""
    claims: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def is_admin(self) -> bool:
        return "admin" in self.scope.split()

    def has_scope(self, scope: str) -> bool:
        return scope in self.scope.split()


class AccessTokenVerifier:
    def __init__(
        self,
        secret: str,
        *,
        issuer: str,
        audience: str,
        algorithm: str = "HS256",
    ) -> None:
        cleaned = str(secret or "").strip()
        if not cleaned:
            raise TokenInvalid("jwt secret is not configured")
        issuer_value = str(issuer or "").strip()
        audience_value = str(audience or "").strip()
        if not issuer_value:
            raise TokenInvalid("issuer is not configured")
        if not audience_value:
            raise TokenInvalid("audience is not configured")
        self._secret = cleaned
        self._algorithm = algorithm
        self._issuer = issuer_value
        self._audience = audience_value

    def decode(self, token: str) -> AccessToken:
        raw = str(token or "").strip()
        if not raw:
            raise TokenInvalid("empty token")
        try:
            payload = jwt.decode(
                raw,
                self._secret,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
                options={"verify_signature": True, "verify_aud": True, "verify_exp": True, "verify_iss": True},
            )
        except JWTError as exc:
            raise TokenInvalid("invalid token") from exc
        if not isinstance(payload, dict):
            raise TokenInvalid("invalid token")
        if str(payload.get("token_use") or "").strip() != TOKEN_USE:
            raise TokenInvalid("token_use_invalid")
        subject = str(payload.get("sub") or "").strip()
        if not subject:
            raise TokenInvalid("missing sub")
        sid = str(payload.get("sid") or "").strip()
        if not sid:
            raise SidRequired("missing sid")
        aud = payload.get("aud")
        if isinstance(aud, (list, tuple)):
            audience = str(aud[0] if aud else "")
        else:
            audience = str(aud or "")
        return AccessToken(
            sub=subject,
            sid=sid,
            token=raw,
            scope=str(payload.get("scope") or ""),
            client_id=str(payload.get("client_id") or "").strip(),
            iss=str(payload.get("iss") or ""),
            aud=audience,
            claims=dict(payload),
        )
