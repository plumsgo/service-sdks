"""Identity events published by Auth70. Unknown or incomplete events parse to None."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError


SESSION_REVOKED = "identity.session.revoked.v1"
USER_SESSIONS_REVOKED = "identity.user.sessions_revoked.v1"
USER_DISABLED = "identity.user.disabled.v1"
REFRESH_REUSE = "identity.refresh_token_reuse_detected.v1"

IDENTITY_EVENTS = frozenset(
    {
        SESSION_REVOKED,
        USER_SESSIONS_REVOKED,
        USER_DISABLED,
        REFRESH_REUSE,
    }
)


class IdentitySessionRevoked(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["identity.session.revoked.v1"]
    sid: str = Field(min_length=1)
    user_id: Optional[str] = None
    reason: Optional[str] = None
    occurred_at: Optional[int] = Field(default=None, ge=0)


class IdentityUserSessionsRevoked(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["identity.user.sessions_revoked.v1"]
    user_id: str = Field(min_length=1)
    reason: Optional[str] = None
    count: Optional[int] = Field(default=None, ge=0)
    occurred_at: Optional[int] = Field(default=None, ge=0)


class IdentityUserDisabled(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["identity.user.disabled.v1"]
    user_id: str = Field(min_length=1)
    reason: Optional[str] = None
    count: Optional[int] = Field(default=None, ge=0)
    occurred_at: Optional[int] = Field(default=None, ge=0)


class IdentityRefreshTokenReuseDetected(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["identity.refresh_token_reuse_detected.v1"]
    sid: str = Field(min_length=1)
    detected_at: Optional[str] = None
    occurred_at: Optional[int] = Field(default=None, ge=0)


IdentityEvent = Union[
    IdentitySessionRevoked,
    IdentityUserSessionsRevoked,
    IdentityUserDisabled,
    IdentityRefreshTokenReuseDetected,
]

_MODELS = {
    SESSION_REVOKED: IdentitySessionRevoked,
    USER_SESSIONS_REVOKED: IdentityUserSessionsRevoked,
    USER_DISABLED: IdentityUserDisabled,
    REFRESH_REUSE: IdentityRefreshTokenReuseDetected,
}


def parse_identity_event(event: Dict[str, Any]) -> Optional[IdentityEvent]:
    if not isinstance(event, dict):
        return None
    model = _MODELS.get(event.get("type"))
    if model is None:
        return None
    try:
        return model.model_validate(event)
    except ValidationError:
        return None
