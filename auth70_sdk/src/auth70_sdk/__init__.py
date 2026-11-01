"""Auth70 SDK.

Verify user access tokens and call the session API with client credentials.
Chat service JWTs are not part of this package.
"""

from auth70_sdk.errors import Auth70Error, OperatorError, SidRequired, TokenInvalid
from auth70_sdk.operator import IntrospectedSession, OperatorClient, SESSIONS_SCOPE
from auth70_sdk.tokens import TOKEN_USE, AccessToken, AccessTokenVerifier, extract_bearer

__version__ = "2.0.0"

__all__ = [
    "SESSIONS_SCOPE",
    "TOKEN_USE",
    "AccessToken",
    "AccessTokenVerifier",
    "Auth70Error",
    "IntrospectedSession",
    "OperatorClient",
    "OperatorError",
    "SidRequired",
    "TokenInvalid",
    "extract_bearer",
]
