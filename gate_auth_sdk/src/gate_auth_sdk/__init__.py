"""Gate Auth SDK.

Accept a user access token or an inbound service ticket, remint an outbound
service ticket, and forward HTTP. User tokens belong in auth70-sdk; service
tickets belong in service-ticket-sdk. This package only composes them.
"""

from gate_auth_sdk.auth import ADMIN_SCOPE, GateAuth
from gate_auth_sdk.errors import ActingRequired, AdminRequired, GateAuthError, MissingToken, ScopeDenied, TokenUseInvalid
from gate_auth_sdk.issuers import parse_issuers
from gate_auth_sdk.principal import Principal
from gate_auth_sdk.upstream import UpstreamError, request, request_json

__version__ = "2.0.0"

__all__ = [
    "ADMIN_SCOPE",
    "ActingRequired",
    "AdminRequired",
    "GateAuth",
    "GateAuthError",
    "MissingToken",
    "ScopeDenied",
    "TokenUseInvalid",
    "Principal",
    "UpstreamError",
    "parse_issuers",
    "request",
    "request_json",
]
