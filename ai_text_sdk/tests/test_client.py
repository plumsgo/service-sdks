import asyncio
import json

import httpx
import pytest

from ai_text_sdk import AiTextClient, AiTextError


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("authorization") == "Bearer svc-token"
    if request.method == "POST" and request.url.path == "/generate":
        body = json.loads(request.content)
        if body.get("scene") == "missing":
            return httpx.Response(404, json={"detail": {"code": "SCENE_NOT_FOUND"}})
        if body.get("scene") == "fail":
            return httpx.Response(
                200,
                json={"success": False, "error": "all presets failed", "error_code": "ALL_PRESETS_FAILED"},
            )
        assert body["scene"] == "ai-post"
        assert body["messages"][0]["role"] == "user"
        return httpx.Response(
            200,
            json={"success": True, "content": "你好", "provider": "openai"},
        )
    return httpx.Response(404, json={"detail": "missing"})


async def _run(fn):
    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://tg") as http:
        await fn(AiTextClient(http, "http://tg"))


def test_generate_and_generate_text():
    async def body(client):
        row = await client.generate(
            "svc-token",
            scene="ai-post",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert row["content"] == "你好"
        text = await client.generate_text(
            "svc-token",
            scene="ai-post",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert text == "你好"

    asyncio.run(_run(body))


def test_missing_token_and_upstream_error():
    async def body(client):
        with pytest.raises(ValueError):
            await client.generate("", scene="ai-post", messages=[{"role": "user", "content": "hi"}])
        with pytest.raises(AiTextError) as exc:
            await client.generate(
                "svc-token",
                scene="missing",
                messages=[{"role": "user", "content": "hi"}],
            )
        assert exc.value.status_code == 404
        with pytest.raises(AiTextError):
            await client.generate_text(
                "svc-token",
                scene="fail",
                messages=[{"role": "user", "content": "hi"}],
            )

    asyncio.run(_run(body))
