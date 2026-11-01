# 服务票 SDK

给**内部微服务**签发、验短命服务 JWT。用户登录票请用 `auth70-sdk`，不要混进本包。

本库**不含**任何业务服务名、audience 表或 FastAPI 依赖。谁可以打谁，由各服务自己声明。

与现网服务票的 claims **同形**：两边互签可以互验。

## 安装

```bash
pip install -e ./sdks/service_ticket_sdk
```

依赖：Python ≥ 3.11、`pydantic`、`python-jose[cryptography]`。

## 票长什么样

| claim | 含义 |
|-------|------|
| `token_use` | **必须**是 `service`；用户 access token 会被拒 |
| `iss` / `sub` | **必须相同**，都是调用方服务名（如 `billing`） |
| `aud` | 目标服务 audience（如 `ledger:internal`） |
| `iat` / `exp` | 签发与过期；TTL 默认 120 秒，上限 300 秒 |
| `scope` | 可选，空格分隔 |
| `acting_kind` | 有 acting 时必填，只认 `user` / `guest` |
| `acting_subject` | 有 acting 时必填 |
| `acting_sid` | 可选；单独出现会整票拒绝 |

共享同一把 `SERVICE_JWT_SECRET`，算法默认 HS256。没有中心签发服务，各服务自己签自己的 `iss`。

## 出站（你调别人）

```python
import os
from service_ticket_sdk import ActingPrincipal, ServiceTickets

tickets = ServiceTickets(os.environ["SERVICE_JWT_SECRET"], issuer="billing")

token = tickets.mint(
    "ledger:internal",
    acting=ActingPrincipal(kind="user", subject_id="u1", auth_session_id="s1"),
    scopes=("ledger:write",),
)
headers = {"Authorization": f"Bearer {token}"}
```

`iss` 写死成你的服务名。`aud` 用对方文档里的 audience，不要自己发明一套还指望互通。

## 入站（别人调你）

```python
from service_ticket_sdk import ServiceTicketError, extract_bearer

ALLOWED_ISSUERS = frozenset({"billing", "bff"})  # 可选；不传则不限制 iss

def require_service(authorization: str | None):
    token = extract_bearer(authorization)
    if not token:
        raise PermissionError("missing_token")
    try:
        return tickets.verify(
            token,
            expected_audience="ledger:internal",  # 你自己的 aud
            allowed_issuers=ALLOWED_ISSUERS,
        )
    except ServiceTicketError as exc:
        raise PermissionError(exc.code) from exc  # 或 HTTP exc.http_status
```

`allowed_issuers` 省略或 `None` = 不限制调用方；传入空集合 = 谁都不认。有共享密钥时，不配白名单等于信任所有持有同一把密钥的服务。

`verify` **成功返回身份，失败抛错**，不要再判断 `None`。

| 异常 | `code` | 建议 HTTP |
|------|--------|-----------|
| `TokenInvalid` | `invalid_token` | 401 |
| `TokenExpired` | `token_expired` | 401 |
| `AudienceMismatch` | `audience_mismatch` | 401 |
| `TokenUseInvalid` | `token_use_invalid` | 401 |
| `IssuerSubjectMismatch` | `issuer_subject_mismatch` | 401 |
| `ActingInvalid` | `acting_invalid` | 401 |
| `IssuerNotAllowed` | `issuer_not_allowed` | 403 |
| `SecretNotConfigured` | `jwt_secret_not_configured` | 503 |
| `TtlInvalid` | `ttl_invalid` | 400（签发侧） |

**信任图不要做成全局表。** 账本服务可以认 `billing`，不必认 `room`。

## 和用户票的边界

- 浏览器 / 用户 JWT → Auth70
- 服务调服务 → 本库
- 用户 JWT **不要**转发给下游。需要「替谁办事」时写 `acting_*`，由网关或 BFF 验过用户票后再签服务票。

## 和别的服务互通时

audience 由各服务自己声明（例如 `ledger:internal`）。对方要把你的 `iss` 加进它的 `allowed_issuers`，你也要把对方加进自己的白名单，并共用同一把 `SERVICE_JWT_SECRET`。

## 不是什么

- 不是 OAuth / JWKS / mTLS / SPIFFE
- 不提供 refresh、operator、服务发现
- 不规定 HTTP 路径或错误码
