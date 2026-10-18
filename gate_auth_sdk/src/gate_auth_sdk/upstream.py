from typing import Any, Optional

import httpx


class UpstreamError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def _detail_from_response(response: httpx.Response) -> Any:
    try:
        body = response.json()
    except Exception:
        return response.text or response.reason_phrase
    return body.get("detail", body.get("message", body))


async def request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    token: str,
    *,
    json: Optional[dict] = None,
    params: Any = None,
    timeout: Optional[float] = None,
) -> httpx.Response:
    response = await client.request(
        method,
        url,
        headers={"Authorization": f"Bearer {token}"},
        json=json,
        params=params,
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise UpstreamError(response.status_code, _detail_from_response(response))
    return response


async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    token: str,
    *,
    json: Optional[dict] = None,
    params: Any = None,
    timeout: Optional[float] = None,
) -> Any:
    response = await request(
        client,
        method,
        url,
        token,
        json=json,
        params=params,
        timeout=timeout,
    )
    if not response.content:
        return None
    return response.json()
