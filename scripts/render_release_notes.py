#!/usr/bin/env python3
"""Render audited GitHub Release notes from the current changelog entry."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


def current_version() -> str:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"(?m)^version: ([^\n]+)$", skill)
    if not match:
        raise ValueError("SKILL.md 缺少 version")
    return match.group(1)


def changelog_entry(version: str) -> str:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"(?ms)^## {re.escape(version)}\s*-\s*[^\n]+\n(?P<body>.*?)(?=^##\s|\Z)",
        changelog,
    )
    if not match:
        raise ValueError(f"CHANGELOG.md 缺少 {version} 条目")
    body = match.group("body").strip()
    if not body:
        raise ValueError(f"CHANGELOG.md 的 {version} 条目为空")
    return body


def render(version: str | None = None) -> str:
    resolved_version = version or current_version()
    changes = changelog_entry(resolved_version)
    return f"""# ReviewWrite v{resolved_version}

## 本版更新

{changes}

## 安装与安全

1. 下载或安装前先核对官方仓库、Release tag、SHA-256 和发布 attestation。
2. 已存在 ReviewWrite 时不得覆盖；先报告已安装版本和路径，再按宿主平台的原生流程升级。
3. 安装后确认 `review-write` 可被发现。平台不支持或权限不足时停止并说明原因。
4. 运行时包只包含 `SKILL.md`、参考资料和本地预检脚本；预检脚本不联网、不读取凭证、不修改输入文件。完整边界见 `SECURITY.md`。

## 已验证

- 本 Release workflow 已在打包前执行结构校验与单元测试。
- Release assets 包含 `.skill`、SHA-256 校验文件和可复制安装提示；`.skill` 另有 GitHub artifact attestation。

## 已知边界

- 预检只定位确定性泄漏与风格信号，不能替代事实、引用、法律或学术专业复核。
- `--context`/`--genre` 只对声明的合法语境放宽相应信号；降级为 warning 后仍须人工确认。
"""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成 ReviewWrite GitHub Release 说明")
    parser.add_argument("--version", help="目标版本；默认读取 SKILL.md")
    args = parser.parse_args(argv)
    try:
        print(render(args.version))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
