# Gate Auth SDK

给**对外入口**用：同时认用户 access token 和打给本门的服务票，收成同一种人，再签一张下游服务票去转发。用户票请用 `auth70-sdk`，服务票请用 `service-ticket-sdk`，本包只做组装。

内网领域服务不要装。只认服务票的继续用 `service-ticket-sdk`；只认用户票的继续用 `auth70-sdk`。

本库**不含**任何业务服务名、人物号段或下游路径。谁可以进门、出站打谁，由各扇门自己声明。

## 安装

```bash
pip install -e ./sdks/auth70_sdk
pip install -e ./sdks/service_ticket_sdk
pip install -e ./sdks/gate_auth_sdk[fastapi]
```

依赖：Python ≥ 3.11、前两个 SDK、`httpx`、`python-jose`。FastAPI 依赖是可选 extra。

## 入站

```python
from gate_auth_sdk import GateAuth, parse_issuers

auth = GateAuth(
    issuer="figure-gate",
    audience="figure-gate:internal",
    user_secret=USER_JWT_SECRET,
    service_secret=SERVICE_JWT_SECRET,
    user_issuer="http://localhost:8777",
    user_audience="gates",
    allowed_issuers=parse_issuers("board,chat"),  # 空集合 = 不认任何服务调用方
)

principal = auth.authenticate(authorization_header)
# principal.sub / sid / admin / via / caller
```

先看未校验的 `token_use`。`service` 走服务票（`aud` 必须是本门，`iss` 必须在白名单）；`access` 交给 Auth70（验 `iss`、平台 `aud`、必有 `sid`）。其余拒。用户 JWT **不会**转发给下游。管理员看用户票的 `scope`，不看 `roles`。

`allowed_issuers=None` = 不限制调用方；传入空集合 = 谁都不认。有共享密钥时，不配白名单等于信任所有持有同一把密钥的服务。

管理员机器任务可以不带 `acting`。需要「替谁办事」时，入站服务票写 `acting_*`，出站再带上。

## 出站

```python
token = auth.ticket_for(principal, "figures:internal")
```

`iss` 写死成本门。有 `principal.sub` 时带 `acting`（kind 固定 `user`）。管理员带 `admin` scope。

## FastAPI

```python
from gate_auth_sdk.deps import GateAuthDeps

deps = GateAuthDeps(auth)

@app.get("/me")
async def me(user = Depends(deps.require_user)):
    ...
```

`require_principal` 允许没有 `acting` 的管理员机器票。`require_user` 必须有 `sub`。`require_admin` 只看管理员。

## 转发

```python
from gate_auth_sdk import request_json

body = await request_json(http, "GET", url, token, timeout=30)
```

4xx/5xx 抛 `UpstreamError`，`status_code` 和 `detail` 从上游响应取出。空 body 的 `request_json` 返回 `None`。

## 不是什么

- 不是第三种身份协议，不发明 claims
- 不提供 refresh、运营台、服务发现
- 不规定业务 HTTP 路径
