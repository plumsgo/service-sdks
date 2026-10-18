# ChatApp Python SDKs

HTTP / auth client libraries for ChatApp microservices. Each package is a standalone setuptools project under its own subdirectory.

## Install from GitHub

Pin a **tag** or **commit** (do not rely on floating branches in production).

In a microservice `requirements.txt`:

```text
-r https://raw.githubusercontent.com/plumsgo/chatapp-sdks/v2.0.0/requirements-from-git.txt
```

That file lists all five SDKs in an order that satisfies cross-package dependencies. Services that only need a subset may still include the whole file (harmless extra packages) or copy individual lines from it.

Example single package (PEP 508):

```text
service-ticket-sdk @ git+https://github.com/plumsgo/chatapp-sdks.git@v2.0.0#subdirectory=service_ticket_sdk
```

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
