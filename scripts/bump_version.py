#!/usr/bin/env python3
"""Synchronize ReviewWrite version fields. Dry-run unless --apply is given."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Sequence

from reviewwrite_update import Version


ROOT = Path(__file__).resolve().parents[1]


def next_version(current: Version, kind: str) -> Version:
    if kind == "patch":
        return Version(current.major, current.minor, current.patch + 1)
    if kind == "minor":
        return Version(current.major, current.minor + 1, 0)
    if kind == "major":
        return Version(current.major + 1, 0, 0)
    raise ValueError(f"未知版本变化: {kind}")


def current_versions() -> dict[str, str]:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    package = (ROOT / "scripts" / "package_skill.py").read_text(encoding="utf-8")
    updater = (ROOT / "scripts" / "reviewwrite_update.py").read_text(encoding="utf-8")
    return {
        "SKILL.md": re.search(r"(?m)^version: ([^\n]+)$", skill).group(1),
        "skills/review-write/SKILL.md": re.search(
            r"(?m)^version: ([^\n]+)$",
            (ROOT / "skills" / "review-write" / "SKILL.md").read_text(encoding="utf-8"),
        ).group(1),
        "package_skill.py": re.search(r'(?m)^VERSION = "([^"]+)"$', package).group(1),
        "reviewwrite_update.py": re.search(r'ReviewWrite-Updater/([0-9.]+)', updater).group(1),
        "compatibility.json": json.loads((ROOT / "compatibility.json").read_text())["reviewwrite_version"],
        "release-policy.json": json.loads((ROOT / "release-policy.json").read_text())["current_version"],
    }


def synchronized_current() -> Version:
    versions = current_versions()
    unique = set(versions.values())
    if len(unique) != 1:
        details = ", ".join(f"{name}={value}" for name, value in versions.items())
        raise ValueError(f"版本字段不一致: {details}")
    return Version.parse(unique.pop())


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"{path.relative_to(ROOT)} 中目标出现 {text.count(old)} 次: {old}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def apply(current: Version, target: Version) -> None:
    old, new = str(current), str(target)
    replace_once(ROOT / "SKILL.md", f"version: {old}", f"version: {new}")
    replace_once(
        ROOT / "skills" / "review-write" / "SKILL.md",
        f"version: {old}",
        f"version: {new}",
    )
    replace_once(
        ROOT / "scripts" / "package_skill.py",
        f'VERSION = "{old}"',
        f'VERSION = "{new}"',
    )
    replace_once(
        ROOT / "scripts" / "reviewwrite_update.py",
        f"ReviewWrite-Updater/{old}",
        f"ReviewWrite-Updater/{new}",
    )
    for filename, key in (
        ("compatibility.json", "reviewwrite_version"),
        ("release-policy.json", "current_version"),
    ):
        path = ROOT / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload[key] = new
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="预览或同步 ReviewWrite 版本")
    parser.add_argument("kind", choices=("patch", "minor", "major"))
    parser.add_argument("--apply", action="store_true", help="实际修改；默认只预览")
    args = parser.parse_args(argv)
    current = synchronized_current()
    target = next_version(current, args.kind)
    print(f"{current} -> {target} ({'APPLY' if args.apply else 'DRY-RUN'})")
    if args.apply:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        if not re.search(rf"(?m)^## \[?{re.escape(str(target))}\]?\b", changelog):
            raise SystemExit(f"CHANGELOG.md 缺少 {target} 条目，未修改版本")
        apply(current, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
