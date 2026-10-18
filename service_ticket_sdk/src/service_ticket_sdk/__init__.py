"""Service-ticket SDK.

Mint and verify short-lived machine JWTs. User access tokens belong in
auth70-sdk, not here.
"""

from service_ticket_sdk.errors import (
    ActingInvalid,
    AudienceMismatch,
    IssuerNotAllowed,
    IssuerSubjectMismatch,
    SecretNotConfigured,
    ServiceTicketError,
    TokenExpired,
    TokenInvalid,
    TokenUseInvalid,
    TtlInvalid,
)
from service_ticket_sdk.tickets import (
    DEFAULT_ALGORITHM,
    DEFAULT_TTL_SECONDS,
    MAX_TTL_SECONDS,
    TOKEN_USE,
    ActingPrincipal,
    ServiceIdentity,
    ServiceTickets,
    extract_bearer,
    mint_service_token,
    verify_service_token,
)

__version__ = "2.0.0"

__all__ = [
    "DEFAULT_ALGORITHM",
    "DEFAULT_TTL_SECONDS",
    "MAX_TTL_SECONDS",
    "TOKEN_USE",
    "ActingInvalid",
    "ActingPrincipal",
    "AudienceMismatch",
    "IssuerNotAllowed",
    "IssuerSubjectMismatch",
    "SecretNotConfigured",
    "ServiceIdentity",
    "ServiceTicketError",
    "ServiceTickets",
    "TokenExpired",
    "TokenInvalid",
    "TokenUseInvalid",
    "TtlInvalid",
    "extract_bearer",
    "mint_service_token",
    "verify_service_token",
]
