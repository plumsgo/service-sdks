"""Mint and verify short-lived service JWTs.

Wire contract:

    token_use = "service"          # required; rejects user access tokens
    iss = sub = calling service
    aud = target service audience
    iat / exp                      # mint ttl in 1..MAX_TTL_SECONDS
    scope                          # optional, space-separated
    acting_kind / acting_subject   # both required if any acting_* is set
    acting_sid                     # optional

This package does not know any service names. Each callee declares its
own ``aud``. ``allowed_issuers`` is optional: omit or pass ``None`` to
accept any caller; a provided collection is an allow-list (empty rejects
everyone).
"""

from __future__ import annotations

import time
from typing import Any, Iterable, Literal, Optional

from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from jose import jwt
from pydantic import BaseModel, ConfigDict, Field

from service_ticket_sdk.errors import (
    ActingInvalid,
    AudienceMismatch,
    IssuerNotAllowed,
    IssuerSubjectMismatch,
    SecretNotConfigured,
    TokenExpired,
    TokenInvalid,
    TokenUseInvalid,
    TtlInvalid,
)

DEFAULT_TTL_SECONDS = 120
MAX_TTL_SECONDS = 300
DEFAULT_ALGORITHM = "HS256"
TOKEN_USE = "service"
_ACTING_KINDS = frozenset({"user", "guest"})


class ActingPrincipal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["user", "guest"] = "user"
    subject_id: str = Field(min_length=1)
    auth_session_id: Optional[str] = None


class ServiceIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issuer: str
    subject: str
    audience: str
    acting: Optional[ActingPrincipal] = None
    scopes: tuple[str, ...] = ()

    def has_scope(self, scope: str) -> bool:
        wanted = str(scope or "").strip()
        return bool(wanted) and wanted in self.scopes


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


def _require_secret(secret: str) -> str:
    cleaned = str(secret or "").strip()
    if not cleaned:
        raise SecretNotConfigured()
    return cleaned


def _require_ttl(ttl_seconds: int) -> int:
    ttl = int(ttl_seconds)
    if ttl < 1 or ttl > MAX_TTL_SECONDS:
        raise TtlInvalid(f"ttl must be 1..{MAX_TTL_SECONDS}")
    return ttl


def _claim_text(payload: dict[str, Any], key: str) -> str:
    if key not in payload or payload.get(key) is None:
        return ""
    return str(payload.get(key) or "").strip()


def _parse_acting(payload: dict[str, Any]) -> Optional[ActingPrincipal]:
    kind = _claim_text(payload, "acting_kind")
    subject = _claim_text(payload, "acting_subject")
    sid = _claim_text(payload, "acting_sid")
    if not kind and not subject and not sid:
        return None
    if not kind or not subject:
        raise ActingInvalid("acting_incomplete")
    if kind not in _ACTING_KINDS:
        raise ActingInvalid("acting_kind_invalid")
    return ActingPrincipal(
        kind=kind,  # type: ignore[arg-type]
        subject_id=subject,
        auth_session_id=sid or None,
    )


def mint_service_token(
    *,
    secret: str,
    issuer: str,
    audience: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    algorithm: str = DEFAULT_ALGORITHM,
    acting: Optional[ActingPrincipal] = None,
    scopes: Iterable[str] = (),
) -> str:
    cleaned_secret = _require_secret(secret)
    caller = str(issuer or "").strip()
    target = str(audience or "").strip()
    if not caller:
        raise TokenInvalid("missing issuer")
    if not target:
        raise TokenInvalid("missing audience")
    ttl = _require_ttl(ttl_seconds)
    now = int(time.time())
    claims: dict[str, Any] = {
        "token_use": TOKEN_USE,
        "iss": caller,
        "sub": caller,
        "aud": target,
        "iat": now,
        "exp": now + ttl,
    }
    scope = " ".join(
        dict.fromkeys(str(value).strip() for value in scopes if str(value).strip())
    )
    if scope:
        claims["scope"] = scope
    if acting is not None:
        claims["acting_kind"] = acting.kind
        claims["acting_subject"] = acting.subject_id
        if acting.auth_session_id:
            claims["acting_sid"] = acting.auth_session_id
    return jwt.encode(claims, cleaned_secret, algorithm=algorithm)


def verify_service_token(
    token: str,
    *,
    secret: str,
    expected_audience: str,
    allowed_issuers: Optional[Iterable[str]] = None,
    algorithm: str = DEFAULT_ALGORITHM,
) -> ServiceIdentity:
    cleaned_secret = _require_secret(secret)
    raw = str(token or "").strip()
    if not raw:
        raise TokenInvalid("empty token")
    try:
        payload = jwt.decode(
            raw,
            cleaned_secret,
            algorithms=[algorithm],
            audience=expected_audience,
        )
    except ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except JWTClaimsError as exc:
        raise AudienceMismatch() from exc
    except JWTError as exc:
        raise TokenInvalid("invalid_token") from exc
    if not isinstance(payload, dict):
        raise TokenInvalid("invalid_token")
    if _claim_text(payload, "token_use") != TOKEN_USE:
        raise TokenUseInvalid()
    issuer = _claim_text(payload, "iss")
    subject = _claim_text(payload, "sub")
    if not issuer or not subject:
        raise TokenInvalid("missing issuer")
    if issuer != subject:
        raise IssuerSubjectMismatch()
    if allowed_issuers is not None:
        allowed = {str(item) for item in allowed_issuers}
        if issuer not in allowed:
            raise IssuerNotAllowed()
    raw_scopes = str(payload.get("scope") or "").split()
    scopes = tuple(dict.fromkeys(item.strip() for item in raw_scopes if item.strip()))
    return ServiceIdentity(
        issuer=issuer,
        subject=subject,
        audience=expected_audience,
        acting=_parse_acting(payload),
        scopes=scopes,
    )


class ServiceTickets:
    """Bind secret + issuer once. Trust graphs still belong to the callee."""

    def __init__(
        self,
        secret: str,
        issuer: str,
        *,
        algorithm: str = DEFAULT_ALGORITHM,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._secret = _require_secret(secret)
        caller = str(issuer or "").strip()
        if not caller:
            raise TokenInvalid("missing issuer")
        self._issuer = caller
        self._algorithm = algorithm
        self._ttl_seconds = _require_ttl(ttl_seconds)

    @property
    def issuer(self) -> str:
        return self._issuer

    def mint(
        self,
        audience: str,
        *,
        acting: Optional[ActingPrincipal] = None,
        scopes: Iterable[str] = (),
        ttl_seconds: Optional[int] = None,
    ) -> str:
        return mint_service_token(
            secret=self._secret,
            issuer=self._issuer,
            audience=audience,
            ttl_seconds=self._ttl_seconds if ttl_seconds is None else ttl_seconds,
            algorithm=self._algorithm,
            acting=acting,
            scopes=scopes,
        )

    def verify(
        self,
        token: str,
        *,
        expected_audience: str,
        allowed_issuers: Optional[Iterable[str]] = None,
    ) -> ServiceIdentity:
        return verify_service_token(
            token,
            secret=self._secret,
            expected_audience=expected_audience,
            allowed_issuers=allowed_issuers,
            algorithm=self._algorithm,
        )
