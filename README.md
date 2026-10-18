# ChatApp Python SDKs

HTTP / auth client libraries for ChatApp microservices. Each package is a standalone setuptools project under its own subdirectory.

## Install from GitHub

Pin a **tag** or **commit** (do not rely on floating branches in production).

```text
# All SDKs (gate services, figure_gate, etc.)
-r https://raw.githubusercontent.com/plumsgo/chatapp-sdks/v2.0.0/requirements-from-git.txt

# Or a single package
-r https://raw.githubusercontent.com/plumsgo/chatapp-sdks/v2.0.0/requirements-service-ticket-sdk.txt
```

Equivalent direct reference (PEP 508):

```text
service-ticket-sdk @ git+https://github.com/plumsgo/chatapp-sdks.git@v2.0.0#subdirectory=service_ticket_sdk
```

### Bundles

| File | Packages |
|------|----------|
| `requirements-from-git.txt` | All five SDKs (install order respects cross-deps) |
| `requirements-service-ticket-sdk.txt` | `service-ticket-sdk` |
| `requirements-auth70-service-ticket.txt` | `auth70-sdk`, `service-ticket-sdk` |
| `requirements-gate-stack.txt` | `auth70-sdk`, `service-ticket-sdk`, `gate-auth-sdk[fastapi]` |
| `requirements-bot-sdks.txt` | `service-ticket-sdk`, `ai-text-sdk` |
| `requirements-ticket-and-storage.txt` | `service-ticket-sdk`, `storage-sdk` |
| `requirements-gate-and-storage.txt` | Gate stack + `storage-sdk` (`profile_gate`) |

When installing `gate-auth-sdk` from Git, list `auth70-sdk` and `service-ticket-sdk` first (or use a bundle file above) so pip does not try to resolve them from PyPI.

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
3. Update microservice `requirements.txt` refs to the new tag.
