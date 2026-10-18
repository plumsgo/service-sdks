from auth70_sdk import (
    IDENTITY_EVENTS,
    IdentitySessionRevoked,
    parse_identity_event,
)


def test_known_events_parse_and_unknown_events_do_not():
    event = parse_identity_event(
        {"type": "identity.session.revoked.v1", "sid": "s1", "user_id": "u1"}
    )
    assert isinstance(event, IdentitySessionRevoked)
    assert event.sid == "s1"
    assert parse_identity_event({"type": "identity.session.revoked.v1"}) is None
    assert parse_identity_event({"type": "other", "sid": "s1"}) is None
    assert parse_identity_event("nope") is None
    assert len(IDENTITY_EVENTS) == 4


def test_user_and_reuse_events():
    disabled = parse_identity_event({"type": "identity.user.disabled.v1", "user_id": "u1", "count": 2})
    reuse = parse_identity_event(
        {"type": "identity.refresh_token_reuse_detected.v1", "sid": "s1", "detected_at": "t"}
    )
    assert disabled.user_id == "u1"
    assert reuse.sid == "s1"
