import asyncio
import json

import httpx
import pytest

from storage_sdk import StorageClient, StorageError


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("authorization") == "Bearer svc-token"
    path = request.url.path
    if request.method == "POST" and path == "/objects":
        body = json.loads(request.content)
        assert body["channel"] == "generated"
        assert body["namespace"] == "images"
        assert "requested_by" not in body
        return httpx.Response(
            201,
            json={"id": "o1", "status": "pending", "upload": {"url": "http://up"}},
        )
    if request.method == "POST" and path == "/objects/o1/complete":
        return httpx.Response(200, json={"id": "o1", "status": "ready"})
    if request.method == "GET" and path == "/objects/o1":
        return httpx.Response(200, json={"id": "o1", "status": "ready"})
    if request.method == "POST" and path == "/objects/urls":
        body = json.loads(request.content)
        urls = {item: {"url": f"http://cdn/{item}"} for item in body["object_ids"]}
        return httpx.Response(200, json={"urls": urls, "failed": {}})
    if request.method == "DELETE" and path == "/objects/o1":
        return httpx.Response(204)
    if request.method == "POST" and path == "/objects/delete":
        body = json.loads(request.content)
        assert body["object_ids"] == ["o1", "o2"]
        return httpx.Response(204)
    return httpx.Response(404, json={"detail": "missing"})


async def _run(fn):
    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://st") as http:
        await fn(StorageClient(http, "http://st"))


def test_issue_complete_get_sign_delete():
    async def body(client):
        issued = await client.issue_upload(
            "svc-token",
            channel="generated",
            namespace="images",
            content_type="image/png",
        )
        assert issued["upload"]["url"] == "http://up"
        completed = await client.complete("svc-token", "o1")
        assert completed["status"] == "ready"
        row = await client.get_object("svc-token", "o1")
        assert row["id"] == "o1"
        signed = await client.sign_urls("svc-token", ["o1"])
        assert signed["urls"]["o1"]["url"] == "http://cdn/o1"
        assert signed["failed"] == {}
        await client.delete("svc-token", "o1")
        await client.delete("svc-token", ["o1", "o2"])

    asyncio.run(_run(body))


def test_missing_token_and_upstream_error():
    async def body(client):
        with pytest.raises(ValueError):
            await client.get_object("", "o1")
        with pytest.raises(StorageError) as exc:
            await client.complete("svc-token", "missing")
        assert exc.value.status_code == 404

    asyncio.run(_run(body))
