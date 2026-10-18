import httpx
import pytest

from auth70_sdk import OperatorClient, OperatorError


def _client(handler) -> OperatorClient:
    return OperatorClient(
        "http://auth.test",
        "operator",
        "secret",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.asyncio
async def test_introspect_exchanges_client_credentials_once():
    calls = {"token": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/token":
            calls["token"] += 1
            assert request.content
            return httpx.Response(200, json={"access_token": "op-token", "expires_in": 120})
        if request.url.path == "/internal/v1/sessions/introspect":
            assert request.headers["authorization"] == "Bearer op-token"
            return httpx.Response(
                200,
                json={"sessions": {"s1": {"active": True, "sid": "s1", "user_id": "u1"}}},
            )
        return httpx.Response(404)

    client = _client(handler)
    first = await client.introspect(["s1", "s1", ""])
    second = await client.introspect(["s1"])
    assert first["s1"].active is True
    assert first["s1"].user_id == "u1"
    assert second["s1"].sid == "s1"
    assert calls["token"] == 1
    assert await client.introspect([]) == {}


@pytest.mark.asyncio
async def test_revoke_and_list_use_the_session_api():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.raw_path.decode().split("?", 1)[0]
        if path == "/oauth/token":
            return httpx.Response(200, json={"access_token": "op-token", "expires_in": 120})
        seen.append((request.method, path))
        if path.endswith("/users/u%201/revoke"):
            return httpx.Response(200, json={"user_id": "u 1", "revoked": 2})
        if path == "/internal/v1/sessions":
            return httpx.Response(200, json={"sessions": [{"sid": "s1", "active": True}]})
        return httpx.Response(200, json={"sid": "s/1", "revoked": True})

    client = _client(handler)
    revoked = await client.revoke_session("s/1", reason="user_logout")
    all_devices = await client.revoke_user("u 1", reason="user_logout_all")
    listed = await client.list_sessions(user_id="u1")
    assert revoked["revoked"] is True
    assert all_devices["revoked"] == 2
    assert listed[0]["sid"] == "s1"
    assert seen[0] == ("POST", "/internal/v1/sessions/s%2F1/revoke")
    assert seen[1][0] == "POST"


@pytest.mark.asyncio
async def test_token_endpoint_failure_is_operator_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    client = _client(handler)
    with pytest.raises(OperatorError) as caught:
        await client.introspect(["s1"])
    assert caught.value.status_code == 401
