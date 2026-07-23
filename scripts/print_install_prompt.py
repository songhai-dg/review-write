#!/usr/bin/env python3
"""Print the copy-paste installation prompt for the official repository."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def repository(configured: str | None) -> str:
    value = configured
    if value is None:
        policy = json.loads((ROOT / "release-policy.json").read_text(encoding="utf-8"))
        value = policy.get("repository")
    if not value:
        raise ValueError("尚未配置官方仓库；请使用 --repo owner/repo")
    if not REPOSITORY_RE.fullmatch(value):
        raise ValueError("官方仓库必须使用 owner/repo 格式")
    return value


def render(repo: str) -> str:
    url = f"https://github.com/{repo}"
    return (
        f"请从官方仓库 {url} 安装 ReviewWrite Skill。先确认来源可信并检查是否已有 ReviewWrite；已有版本时报告版本和路径，不得覆盖。再按当前平台的原生 Skill 安装或导入机制执行，并验证 `review-write` 可被发现；平台不支持或权限不足时说明原因后停止。"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成 ReviewWrite 一句话安装指令")
    parser.add_argument("--repo", help="官方 GitHub 仓库，格式 owner/repo")
    args = parser.parse_args(argv)
    try:
        print(render(repository(args.repo)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
