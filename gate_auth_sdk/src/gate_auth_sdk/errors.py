"""Gate-auth errors. These are not HTTP exceptions; callers map them."""


class GateAuthError(Exception):
    """Base error for inbound authentication at a gate."""

    code = "gate_auth_error"
    http_status = 401

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.code)


class MissingToken(GateAuthError):
    code = "missing_token"


class TokenUseInvalid(GateAuthError):
    code = "token_use_invalid"


class ActingRequired(GateAuthError):
    """The caller is authenticated but is not acting as a user."""

    code = "acting_required"


class AdminRequired(GateAuthError):
    code = "admin_required"
    http_status = 403


class ScopeDenied(GateAuthError):
    code = "permission_denied"
    http_status = 403
