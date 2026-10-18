from typing import Any, Optional

import httpx

from storage_sdk.errors import StorageError


def _detail_from_response(response: httpx.Response) -> Any:
    try:
        body = response.json()
    except Exception:
        return response.text or response.reason_phrase
    if isinstance(body, dict):
        return body.get("detail", body.get("message", body))
    return body


async def request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    token: str,
    *,
    json: Optional[dict] = None,
    timeout: Optional[float] = None,
) -> httpx.Response:
    response = await client.request(
        method,
        url,
        headers={"Authorization": f"Bearer {token}"},
        json=json,
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise StorageError(response.status_code, _detail_from_response(response))
    return response


async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    token: str,
    *,
    json: Optional[dict] = None,
    timeout: Optional[float] = None,
) -> Any:
    response = await request(
        client,
        method,
        url,
        token,
        json=json,
        timeout=timeout,
    )
    if not response.content:
        return None
    return response.json()
