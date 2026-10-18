"""Accept a user token or inbound service ticket; remint an outbound ticket."""
from __future__ import annotations

from typing import Iterable, Optional, Sequence

from jose import jwt

from auth70_sdk import AccessTokenVerifier
from service_ticket_sdk import ActingPrincipal, ServiceTickets, TOKEN_USE, extract_bearer

from gate_auth_sdk.errors import ActingRequired, AdminRequired, MissingToken, ScopeDenied, TokenUseInvalid
from gate_auth_sdk.principal import Principal

ADMIN_SCOPE = "admin"
USER_TOKEN_USE = "access"


def _peek_use(token: str) -> str:
    try:
        return str(jwt.get_unverified_claims(token).get("token_use") or "").strip()
    except Exception:
        return ""


class GateAuth:
    """One gate's inbound and outbound tickets.

    ``allowed_issuers=None`` accepts any service caller that holds the shared
    secret. An iterable, including empty, is an allow-list. Empty rejects every
    inbound service ticket.
    """

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        user_secret: str,
        service_secret: str,
        user_issuer: str,
        user_audience: str,
        allowed_issuers: Optional[Iterable[str]] = (),
        user_algorithm: str = "HS256",
        service_algorithm: str = "HS256",
        admin_scope: str = ADMIN_SCOPE,
    ) -> None:
        self._audience = str(audience or "").strip()
        if not self._audience:
            raise ValueError("audience is required")
        self._admin_scope = str(admin_scope or "").strip() or ADMIN_SCOPE
        self._user_tokens = AccessTokenVerifier(
            user_secret,
            issuer=user_issuer,
            audience=user_audience,
            algorithm=user_algorithm,
        )
        self._tickets = ServiceTickets(
            service_secret,
            issuer,
            algorithm=service_algorithm,
        )
        if allowed_issuers is None:
            self._allowed_issuers: Optional[frozenset[str]] = None
        else:
            self._allowed_issuers = frozenset(
                str(item).strip() for item in allowed_issuers if str(item).strip()
            )

    @property
    def issuer(self) -> str:
        return self._tickets.issuer

    @property
    def audience(self) -> str:
        return self._audience

    def authenticate(self, authorization: Optional[str]) -> Principal:
        token = extract_bearer(authorization)
        if not token:
            raise MissingToken()
        return self.authenticate_token(token)

    def authenticate_token(self, token: str) -> Principal:
        raw = str(token or "").strip()
        if not raw:
            raise MissingToken()
        token_use = _peek_use(raw)
        if token_use == TOKEN_USE:
            identity = self._tickets.verify(
                raw,
                expected_audience=self._audience,
                allowed_issuers=self._allowed_issuers,
            )
            acting = identity.acting
            return Principal(
                sub=acting.subject_id if acting else None,
                sid=acting.auth_session_id if acting else None,
                admin=identity.has_scope(self._admin_scope),
                via="service",
                caller=identity.issuer,
                scopes=frozenset(identity.scopes or ()),
            )
        if token_use != USER_TOKEN_USE:
            raise TokenUseInvalid()

        user = self._user_tokens.decode(raw)
        return Principal(
            sub=user.sub,
            sid=user.sid,
            admin=user.is_admin(),
            via="user",
            caller="user",
        )

    def require_user(self, authorization: Optional[str]) -> Principal:
        principal = self.authenticate(authorization)
        if not principal.sub:
            raise ActingRequired()
        return principal

    def require_admin(self, authorization: Optional[str]) -> Principal:
        principal = self.authenticate(authorization)
        if not principal.admin:
            raise AdminRequired()
        return principal

    def ticket_for(
        self,
        principal: Principal,
        audience: str,
        *,
        acting: bool = True,
        scopes: Optional[Sequence[str]] = None,
    ) -> str:
        if scopes is None:
            minted = set(principal.scopes)
        else:
            minted = {str(item).strip() for item in scopes if str(item).strip()}
        if principal.admin:
            minted.add(self._admin_scope)
        acting_principal = None
        if acting and principal.sub:
            acting_principal = ActingPrincipal(
                kind="user",
                subject_id=principal.sub,
                auth_session_id=principal.sid,
            )
        return self._tickets.mint(audience, acting=acting_principal, scopes=tuple(sorted(minted)))
