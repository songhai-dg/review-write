#!/usr/bin/env python3
"""Print the copy-paste installation prompt for the canonical source."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
OFFICIAL_REPOSITORY = "songhai-dg/review-write"
DOMESTIC_MIRROR_URL = "https://gitee.com/cufe01/songhai-dg"


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
    fallback = ""
    if repo == OFFICIAL_REPOSITORY:
        fallback = f"如当前网络无法访问 GitHub，使用同步镜像 {DOMESTIC_MIRROR_URL}。"
    return (
        f"请从官方仓库 {url} 安装 ReviewWrite Skill；{fallback}如果当前智能体已经安装，不要重复安装，"
        "也不要搜索或替换成名称相近的其他技能。请使用所在平台自己的 Skill 安装或导入机制；"
        "如果仓库已在当前目录，直接以当前目录为安装来源。平台不支持、没有权限或无法访问来源时，说明限制并停止。"
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
