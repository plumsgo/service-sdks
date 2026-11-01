#!/usr/bin/env python3
"""按包发版：升指定包的 version，并打 `{name}-v{version}` tag。

默认只打点名的包。auth70-sdk 与 service-ticket-sdk 互不依赖，
可单独发。gate-auth-sdk 依赖这两者；只有接口变了才用
``--with-dependents`` 顺带打它。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/plumsgo/service-sdks.git"
PINS_FILE = ROOT / "requirements-from-git.txt"
VERSION_RE = re.compile(r'^version = "([^"]+)"$', re.M)

PACKAGES: dict[str, dict[str, object]] = {
    "auth70-sdk": {
        "dir": "auth70_sdk",
        "extras": "",
        "depends": (),
    },
    "service-ticket-sdk": {
        "dir": "service_ticket_sdk",
        "extras": "",
        "depends": (),
    },
    "storage-sdk": {
        "dir": "storage_sdk",
        "extras": "",
        "depends": (),
    },
    "ai-text-sdk": {
        "dir": "ai_text_sdk",
        "extras": "",
        "depends": (),
    },
    "gate-auth-sdk": {
        "dir": "gate_auth_sdk",
        "extras": "[fastapi]",
        "depends": ("auth70-sdk", "service-ticket-sdk"),
    },
}
PIN_ORDER = (
    "auth70-sdk",
    "service-ticket-sdk",
    "storage-sdk",
    "ai-text-sdk",
    "gate-auth-sdk",
)


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=check,
        text=True,
        capture_output=True,
    )


def package_dir(name: str) -> Path:
    meta = PACKAGES[name]
    return ROOT / str(meta["dir"])


def read_version(name: str) -> str:
    data = tomllib.loads(package_dir(name).joinpath("pyproject.toml").read_text(encoding="utf-8"))
    version = str(data["project"]["version"])
    if not version:
        raise SystemExit(f"{name}: pyproject 缺少 version")
    return version


def tag_name(name: str, version: str | None = None) -> str:
    return f"{name}-v{version or read_version(name)}"


def tag_exists(tag: str) -> bool:
    return _git("rev-parse", "-q", "--verify", f"refs/tags/{tag}", check=False).returncode == 0


def published_ref(name: str, *, version: str | None = None, prefer: str | None = None) -> str:
    if prefer:
        return prefer
    tag = tag_name(name, version)
    return tag if tag_exists(tag) else "v2.0.0"


def pep508(name: str, *, version: str | None = None, tag: str | None = None) -> str:
    meta = PACKAGES[name]
    extras = str(meta["extras"])
    ref = published_ref(name, version=version, prefer=tag)
    return (
        f"{name}{extras} @ git+{REPO}@{ref}"
        f"#subdirectory={meta['dir']}"
    )


def bump_semver(version: str, part: str) -> str:
    bits = version.split(".")
    if len(bits) != 3 or not all(bit.isdigit() for bit in bits):
        raise SystemExit(f"无法递增非 x.y.z 版本：{version}")
    major, minor, patch = (int(bit) for bit in bits)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit(f"未知 bump：{part}")


def write_version(name: str, version: str) -> None:
    path = package_dir(name) / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    if not VERSION_RE.search(text):
        raise SystemExit(f"{path}: 找不到 version 行")
    path.write_text(VERSION_RE.sub(f'version = "{version}"', text, count=1), encoding="utf-8")


def render_pins(*, refs: dict[str, str] | None = None) -> str:
    refs = refs or {}
    return "\n".join(pep508(name, tag=refs.get(name)) for name in PIN_ORDER) + "\n"


def write_pins(*, refs: dict[str, str] | None = None) -> None:
    PINS_FILE.write_text(render_pins(refs=refs), encoding="utf-8")


def dependents_of(name: str) -> tuple[str, ...]:
    return tuple(
        other
        for other, meta in PACKAGES.items()
        if name in tuple(meta.get("depends") or ())
    )


def resolve_names(requested: Iterable[str], *, with_dependents: bool) -> list[str]:
    names: list[str] = []
    for raw in requested:
        name = raw.strip()
        if name not in PACKAGES:
            known = ", ".join(PIN_ORDER)
            raise SystemExit(f"未知包 {name!r}。可选：{known}")
        if name not in names:
            names.append(name)
        if with_dependents:
            for dep in dependents_of(name):
                if dep not in names:
                    names.append(dep)
    return [name for name in PIN_ORDER if name in names]


def assert_clean() -> None:
    status = _git("status", "--porcelain").stdout
    if status.strip():
        raise SystemExit("工作区不干净，先提交或 stash 再 cut")


def create_tag(name: str, version: str, *, ref: str) -> str:
    tag = tag_name(name, version)
    exists = _git("rev-parse", "-q", "--verify", f"refs/tags/{tag}", check=False)
    if exists.returncode == 0:
        raise SystemExit(f"tag 已存在：{tag}")
    _git("tag", "-a", tag, ref, "-m", f"{name} {version}")
    return tag


def cmd_pins(_: argparse.Namespace) -> None:
    sys.stdout.write(render_pins())


def cmd_write_pins(_: argparse.Namespace) -> None:
    write_pins()
    print(f"已写入 {PINS_FILE.relative_to(ROOT)}")


def cmd_cut(args: argparse.Namespace) -> None:
    names = resolve_names(args.packages, with_dependents=args.with_dependents)
    if not names:
        raise SystemExit("没有要发的包")
    if not args.allow_dirty:
        assert_clean()
    versions: dict[str, str] = {}
    for name in names:
        current = read_version(name)
        versions[name] = bump_semver(current, args.bump) if args.bump else current
        if args.bump:
            write_version(name, versions[name])
    if args.bump:
        write_pins(refs={name: tag_name(name, versions[name]) for name in names})
        files = [
            str((package_dir(name) / "pyproject.toml").relative_to(ROOT))
            for name in names
        ]
        files.append(str(PINS_FILE.relative_to(ROOT)))
        _git("add", *files)
        title = ", ".join(f"{name} {versions[name]}" for name in names)
        _git("commit", "-m", f"Release {title}.")
    tags = [create_tag(name, versions[name], ref="HEAD") for name in names]
    for name, tag in zip(names, tags):
        print(pep508(name, tag=tag))
    if not args.with_dependents:
        extra = []
        for name in names:
            extra.extend(dependents_of(name))
        extra = [name for name in PIN_ORDER if name in extra and name not in names]
        if extra:
            print(
                "未打依赖本包的包："
                + ", ".join(extra)
                + "。接口变了再 cut，或加 --with-dependents。"
            )
    print("推送提交与 tag：")
    print("  git push origin HEAD")
    print("  git push origin " + " ".join(tags))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按包给本仓库的 SDK 打 tag")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("pins", help="打印当前 pyproject 对应的 PEP 508 行").set_defaults(func=cmd_pins)
    sub.add_parser("write-pins", help="重写 requirements-from-git.txt").set_defaults(func=cmd_write_pins)

    cut = sub.add_parser("cut", help="给指定包打 tag；--bump 时先改 version 并提交")
    cut.add_argument("packages", nargs="+")
    cut.add_argument("--bump", choices=("patch", "minor", "major"))
    cut.add_argument(
        "--with-dependents",
        action="store_true",
        help="顺带打依赖本包的包（目前只有 gate-auth-sdk 依赖另外两个）",
    )
    cut.add_argument("--allow-dirty", action="store_true")
    cut.set_defaults(func=cmd_cut)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise SystemExit(detail or str(exc)) from exc


if __name__ == "__main__":
    main()
