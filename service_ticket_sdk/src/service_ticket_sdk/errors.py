"""Service-ticket errors. These are not HTTP exceptions; callers map them."""


class ServiceTicketError(Exception):
    """Base error for minting or reading a service ticket."""

    code = "service_ticket_error"
    http_status = 401

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.code)


class SecretNotConfigured(ServiceTicketError):
    code = "jwt_secret_not_configured"
    http_status = 503


class TtlInvalid(ServiceTicketError):
    """Mint-side: ttl is below 1 or above MAX_TTL_SECONDS."""

    code = "ttl_invalid"
    http_status = 400


class TokenInvalid(ServiceTicketError):
    """Signature, empty token, or Authorization header is not acceptable."""

    code = "invalid_token"


class TokenExpired(ServiceTicketError):
    code = "token_expired"


class AudienceMismatch(ServiceTicketError):
    code = "audience_mismatch"


class TokenUseInvalid(ServiceTicketError):
    """Missing or non-service token_use. User access tokens fail here."""

    code = "token_use_invalid"


class IssuerSubjectMismatch(ServiceTicketError):
    code = "issuer_subject_mismatch"


class IssuerNotAllowed(ServiceTicketError):
    code = "issuer_not_allowed"
    http_status = 403


class ActingInvalid(ServiceTicketError):
    """acting_* present but incomplete, or acting_kind is not user|guest."""

    code = "acting_invalid"
