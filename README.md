# ChatApp Python SDKs

HTTP / auth client libraries for ChatApp microservices. Each package is a standalone setuptools project under its own subdirectory.

## Install from GitHub

Pin a **tag** or **commit** (do not rely on floating branches in production).

In each microservice `requirements.txt`, list only the SDKs that service needs, one PEP 508 line per package:

```text
service-ticket-sdk @ git+https://github.com/plumsgo/chatapp-sdks.git@v2.0.0#subdirectory=service_ticket_sdk
gate-auth-sdk[fastapi] @ git+https://github.com/plumsgo/chatapp-sdks.git@v2.0.0#subdirectory=gate_auth_sdk
```

When a service uses `gate-auth-sdk`, install `auth70-sdk` and `service-ticket-sdk` from the same tag **before** it in the file so pip does not try to resolve them from PyPI.

`requirements-from-git.txt` in this repo lists all five packages in a safe order; copy lines from it, do not `-r` it from production services unless you intentionally want every SDK.

### Private repository

If this repo is private, use a read-only token when installing:

```text
git+https://x-access-token:TOKEN@github.com/plumsgo/chatapp-sdks.git@v2.0.0#subdirectory=service_ticket_sdk
```

In Docker, pass the token via BuildKit secret or build-arg; do not bake tokens into image layers.

## Local development

```bash
cd auth70_sdk && pip install -e ".[dev]"
```

## Release

1. Bump `version` in each affected `pyproject.toml`.
2. Commit, tag the repo (e.g. `v2.0.0`), push the tag.
3. Update each microservice’s git ref (`@v2.0.0`) on the lines it uses.
