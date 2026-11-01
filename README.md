# Service SDKs

HTTP / auth client libraries for internal microservices. One git repo, five standalone setuptools packages. The packages are not tied to a product. Install and release are per package.

## Install from GitHub

Pin a git tag. Do not use a branch.

The current published snapshot is still the repo-wide tag `v2.0.0`. Until a package has its own tag from `cut`, keep pinning that snapshot:

```text
service-ticket-sdk @ git+https://github.com/plumsgo/service-sdks.git@v2.0.0#subdirectory=service_ticket_sdk
ai-text-sdk @ git+https://github.com/plumsgo/service-sdks.git@v2.0.0#subdirectory=ai_text_sdk
```

After a package is cut, change **only that line** to its package tag:

```text
ai-text-sdk @ git+https://github.com/plumsgo/service-sdks.git@ai-text-sdk-v1.0.1#subdirectory=ai_text_sdk
```

`gate-auth-sdk` depends on `auth70-sdk` and `service-ticket-sdk`. Put those two lines **before** it so pip does not resolve them from PyPI. They do not have to share a tag:

```text
auth70-sdk @ git+https://github.com/plumsgo/service-sdks.git@v2.0.0#subdirectory=auth70_sdk
service-ticket-sdk @ git+https://github.com/plumsgo/service-sdks.git@v2.0.0#subdirectory=service_ticket_sdk
gate-auth-sdk[fastapi] @ git+https://github.com/plumsgo/service-sdks.git@v2.0.0#subdirectory=gate_auth_sdk
```

`requirements-from-git.txt` lists all five in a safe order, currently on `v2.0.0`. Copy the lines you need; do not `-r` the whole file from a production service unless you intentionally want every SDK.

### Private repository

If this repo is private, use a read-only token when installing:

```text
git+https://x-access-token:TOKEN@github.com/plumsgo/service-sdks.git@v2.0.0#subdirectory=service_ticket_sdk
```

In Docker, pass the token via BuildKit secret or build-arg; do not bake tokens into image layers.

## Local development

```bash
cd auth70_sdk && pip install -e ".[dev]"
```

## Release

New versions use `{package-name}-v{version}`, for example `ai-text-sdk-v1.0.1`. Do not create new repo-wide tags. `v2.0.0` stays as the last whole-repo snapshot.

1. Cut only the packages that changed:

   ```bash
   python scripts/release.py cut ai-text-sdk --bump patch
   ```

   `auth70-sdk` and `service-ticket-sdk` are independent. `gate-auth-sdk` is the only dependent; if its imports broke, cut it too, or pass `--with-dependents`.

2. Push the release commit and tags:

   ```bash
   git push origin HEAD
   git push origin ai-text-sdk-v1.0.1
   ```

3. In each microservice, update **only the lines for packages it uses**.

```bash
python scripts/release.py pins          # print current PEP 508 lines
python scripts/release.py write-pins    # refresh requirements-from-git.txt
```
