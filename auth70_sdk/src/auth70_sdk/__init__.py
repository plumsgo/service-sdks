"""Auth70 SDK.

Verify user access tokens, call the session API with client credentials,
and parse identity events. Chat service JWTs are not part of this package.
"""

from auth70_sdk.errors import Auth70Error, OperatorError, SidRequired, TokenInvalid
from auth70_sdk.events import (
    IDENTITY_EVENTS,
    REFRESH_REUSE,
    SESSION_REVOKED,
    USER_DISABLED,
    USER_SESSIONS_REVOKED,
    IdentityEvent,
    IdentityRefreshTokenReuseDetected,
    IdentitySessionRevoked,
    IdentityUserDisabled,
    IdentityUserSessionsRevoked,
    parse_identity_event,
)
from auth70_sdk.operator import IntrospectedSession, OperatorClient, SESSIONS_SCOPE
from auth70_sdk.tokens import TOKEN_USE, AccessToken, AccessTokenVerifier, extract_bearer

__version__ = "2.0.0"

__all__ = [
    "IDENTITY_EVENTS",
    "REFRESH_REUSE",
    "SESSIONS_SCOPE",
    "TOKEN_USE",
    "SESSION_REVOKED",
    "USER_DISABLED",
    "USER_SESSIONS_REVOKED",
    "AccessToken",
    "AccessTokenVerifier",
    "Auth70Error",
    "IdentityEvent",
    "IdentityRefreshTokenReuseDetected",
    "IdentitySessionRevoked",
    "IdentityUserDisabled",
    "IdentityUserSessionsRevoked",
    "IntrospectedSession",
    "OperatorClient",
    "OperatorError",
    "SidRequired",
    "TokenInvalid",
    "extract_bearer",
    "parse_identity_event",
]
