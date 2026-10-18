"""Auth70 SDK errors. These are not HTTP exceptions; callers map them."""


class Auth70Error(Exception):
    """Base error for token verification and the operator client."""


class TokenInvalid(Auth70Error):
    """Signature, expiry, shape, or subject is not acceptable."""


class SidRequired(Auth70Error):
    """Verifier was configured to require sid, and the token has none."""


class OperatorError(Auth70Error):
    """Token exchange or a session API call failed."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
