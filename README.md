# Service SDKs

HTTP / auth client libraries for internal microservices. One git repo, five standalone setuptools packages. The packages are not tied to a product. Install and release are per package.

## Install from GitHub

Pin a **package tag**. Do not use a branch, and do not pin the historical repo-wide tag `v2.0.0`.

Copy only the lines you need from `requirements-from-git.txt`. `gate-auth-sdk` depends on `auth70-sdk` and `service-ticket-sdk`: put those two lines **before** it so pip does not resolve them from PyPI. They do not have to share a version.

```text
auth70-sdk @ git+https://github.com/plumsgo/service-sdks.git@auth70-sdk-v2.0.0#subdirectory=auth70_sdk
service-ticket-sdk @ git+https://github.com/plumsgo/service-sdks.git@service-ticket-sdk-v2.0.0#subdirectory=service_ticket_sdk
storage-sdk @ git+https://github.com/plumsgo/service-sdks.git@storage-sdk-v1.0.1#subdirectory=storage_sdk
ai-text-sdk @ git+https://github.com/plumsgo/service-sdks.git@ai-text-sdk-v1.0.0#subdirectory=ai_text_sdk
gate-auth-sdk[fastapi] @ git+https://github.com/plumsgo/service-sdks.git@gate-auth-sdk-v2.0.0#subdirectory=gate_auth_sdk
```

Do not `-r` the whole file from a production service unless you intentionally want every SDK.

### Private repository

If this repo is private, use a read-only token when installing:

```text
git+https://x-access-token:TOKEN@github.com/plumsgo/service-sdks.git@service-ticket-sdk-v2.0.0#subdirectory=service_ticket_sdk
```

In Docker, pass the token via BuildKit secret or build-arg; do not bake tokens into image layers.

## Local development

```bash
cd auth70_sdk && pip install -e ".[dev]"
```

## Release

New versions use `{package-name}-v{version}`, for example `storage-sdk-v1.0.1`. Do not create new repo-wide tags. `v2.0.0` stays as the last whole-repo snapshot.

1. Cut only the packages that changed:

   ```bash
   python scripts/release.py cut storage-sdk --bump patch
   ```

   `auth70-sdk` and `service-ticket-sdk` are independent. `gate-auth-sdk` is the only dependent; if its imports broke, cut it too, or pass `--with-dependents`.

2. Push the release commit and tags:

   ```bash
   git push origin HEAD
   git push origin storage-sdk-v1.0.1
   ```

3. In each microservice, update **only the lines for packages it uses**.

```bash
python scripts/release.py pins          # print current PEP 508 lines
python scripts/release.py write-pins    # refresh requirements-from-git.txt
```
