import httpx
import pytest

from gate_auth_sdk import UpstreamError, request, request_json


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("authorization") == "Bearer gate-token"
    if request.url.path == "/empty":
        return httpx.Response(204)
    if request.url.path == "/boom":
        return httpx.Response(404, json={"detail": {"code": "missing", "message": "no"}})
    return httpx.Response(200, json={"ok": True})


@pytest.mark.asyncio
async def test_request_json_success_and_empty():
    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://up") as client:
        body = await request_json(client, "GET", "http://up/ok", "gate-token")
        assert body == {"ok": True}
        assert await request_json(client, "DELETE", "http://up/empty", "gate-token") is None


@pytest.mark.asyncio
async def test_request_raises_upstream_error():
    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://up") as client:
        with pytest.raises(UpstreamError) as exc:
            await request(client, "GET", "http://up/boom", "gate-token")
        assert exc.value.status_code == 404
        assert exc.value.detail == {"code": "missing", "message": "no"}
