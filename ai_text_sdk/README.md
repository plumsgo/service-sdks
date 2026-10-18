# AI Text SDK

给调用方打文本生成服务。只认 `POST /generate`，入参是 `scene` + `messages`。票由调用方签发，本包不签服务票、不解释 scene。

## 安装

```bash
pip install -e ./sdks/ai_text_sdk
```

依赖：Python ≥ 3.11、`httpx`。

## 用法

```python
from ai_text_sdk import AiTextClient, AiTextError

client = AiTextClient(http, "http://localhost:9040", timeout=120)
body = await client.generate(
    ticket,
    scene="ai-post",
    messages=[{"role": "user", "content": "你好"}],
)
text = await client.generate_text(
    ticket,
    scene="ai-post",
    messages=[{"role": "user", "content": "你好"}],
)
```

HTTP ≥ 400 抛 `AiTextError`。`generate` 原样返回服务 JSON；`generate_text` 在 `success=false` 时也抛 `AiTextError`。
