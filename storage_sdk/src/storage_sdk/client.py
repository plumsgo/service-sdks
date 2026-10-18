from typing import Optional, Sequence, Union
from uuid import UUID

import httpx

from storage_sdk.http import request, request_json

ObjectId = Union[str, UUID]


def _url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


def _token(token: str) -> str:
    value = str(token or "").strip()
    if not value:
        raise ValueError("storage token is required")
    return value


def _ids(object_ids: Union[ObjectId, Sequence[ObjectId]]) -> list[str]:
    if isinstance(object_ids, (str, UUID)):
        items = [object_ids]
    else:
        items = list(object_ids)
    ids = [str(item).strip() for item in items if str(item).strip()]
    if not ids:
        raise ValueError("object_ids is required")
    return ids


class StorageClient:
    """对象存储网关客户端。票由调用方签发，本类不代传字节到桶。"""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        *,
        timeout: float = 30,
    ) -> None:
        self.http = http
        self.base_url = str(base_url or "").rstrip("/")
        if not self.base_url:
            raise ValueError("base_url is required")
        self.timeout = timeout

    async def issue_upload(
        self,
        token: str,
        *,
        channel: str,
        namespace: str,
        content_type: str,
        size_bytes: Optional[int] = None,
        requested_for_subject: Optional[str] = None,
    ) -> dict:
        body: dict = {
            "channel": channel,
            "namespace": namespace,
            "content_type": content_type,
        }
        if size_bytes is not None:
            body["size_bytes"] = size_bytes
        if requested_for_subject:
            body["requested_for_subject"] = requested_for_subject
        return await request_json(
            self.http,
            "POST",
            _url(self.base_url, "/objects"),
            _token(token),
            json=body,
            timeout=self.timeout,
        )

    async def complete(self, token: str, object_id: ObjectId) -> dict:
        return await request_json(
            self.http,
            "POST",
            _url(self.base_url, f"/objects/{object_id}/complete"),
            _token(token),
            timeout=self.timeout,
        )

    async def get_object(self, token: str, object_id: ObjectId) -> dict:
        return await request_json(
            self.http,
            "GET",
            _url(self.base_url, f"/objects/{object_id}"),
            _token(token),
            timeout=self.timeout,
        )

    async def sign_urls(self, token: str, object_ids: Sequence[ObjectId]) -> dict:
        ids = _ids(object_ids)
        body = await request_json(
            self.http,
            "POST",
            _url(self.base_url, "/objects/urls"),
            _token(token),
            json={"object_ids": ids},
            timeout=self.timeout,
        )
        payload = body or {}
        return {
            "urls": payload.get("urls") or {},
            "failed": payload.get("failed") or {},
        }

    async def delete(self, token: str, object_ids: Union[ObjectId, Sequence[ObjectId]]) -> None:
        ids = _ids(object_ids)
        token = _token(token)
        if len(ids) == 1:
            await request(
                self.http,
                "DELETE",
                _url(self.base_url, f"/objects/{ids[0]}"),
                token,
                timeout=self.timeout,
            )
            return
        await request(
            self.http,
            "POST",
            _url(self.base_url, "/objects/delete"),
            token,
            json={"object_ids": ids},
            timeout=self.timeout,
        )
