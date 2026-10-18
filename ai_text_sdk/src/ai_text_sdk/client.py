from typing import Any, Mapping, Sequence

import httpx

from ai_text_sdk.errors import AiTextError
from ai_text_sdk.http import request_json


def _url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


def _token(token: str) -> str:
    value = str(token or "").strip()
    if not value:
        raise ValueError("ai text token is required")
    return value


def _messages(messages: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for raw in messages or []:
        role = str((raw or {}).get("role") or "").strip()
        if not role:
            raise ValueError("message role is required")
        items.append({"role": role, "content": str((raw or {}).get("content") or "")})
    if not items:
        raise ValueError("messages is required")
    return items


class AiTextClient:
    """文本生成客户端。票由调用方签发，本类不解释 scene。"""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        *,
        timeout: float = 120,
    ) -> None:
        self.http = http
        self.base_url = str(base_url or "").rstrip("/")
        if not self.base_url:
            raise ValueError("base_url is required")
        self.timeout = timeout

    async def generate(
        self,
        token: str,
        *,
        scene: str,
        messages: Sequence[Mapping[str, Any]],
    ) -> dict:
        name = str(scene or "").strip()
        if not name:
            raise ValueError("scene is required")
        body = await request_json(
            self.http,
            "POST",
            _url(self.base_url, "/generate"),
            _token(token),
            json={"scene": name, "messages": _messages(messages)},
            timeout=self.timeout,
        )
        return body if isinstance(body, dict) else {}

    async def generate_text(
        self,
        token: str,
        *,
        scene: str,
        messages: Sequence[Mapping[str, Any]],
    ) -> str:
        body = await self.generate(token, scene=scene, messages=messages)
        if not body.get("success"):
            raise AiTextError(502, body.get("error") or body.get("error_code") or "generation failed")
        return str(body.get("content") or "")
