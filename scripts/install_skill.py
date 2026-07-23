#!/usr/bin/env python3
"""Plan or safely install ReviewWrite for supported Agent Skills clients.

The default is dry-run. Existing destinations are never overwritten.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import package_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "reviewwrite"
LEGACY_SKILL_NAME = "review-write"
COPY_TARGETS = {"codex", "claude", "hermes", "gemini", "copilot", "generic"}
TARGET_CATALOG = (
    {
        "target": "codex",
        "platform": "Codex",
        "scopes": ["user", "project"],
        "completion": "installed-after-apply",
    },
    {
        "target": "claude",
        "platform": "Claude Code",
        "scopes": ["user", "project"],
        "completion": "installed-after-apply",
    },
    {
        "target": "hermes",
        "platform": "Hermes Agent",
        "scopes": ["user"],
        "completion": "installed-after-apply",
    },
    {
        "target": "gemini",
        "platform": "Gemini CLI",
        "scopes": ["user", "project"],
        "completion": "installed-after-apply",
    },
    {
        "target": "copilot",
        "platform": "GitHub Copilot",
        "scopes": ["user", "project"],
        "completion": "installed-after-apply",
    },
    {
        "target": "openclaw",
        "platform": "OpenClaw",
        "scopes": ["user", "project"],
        "completion": "installed-after-apply",
    },
    {
        "target": "workbuddy",
        "platform": "WorkBuddy",
        "scopes": ["user"],
        "completion": "manual-upload-required",
    },
)
ALL_TARGETS = tuple(item["target"] for item in TARGET_CATALOG)
CATALOG_BY_TARGET = {item["target"]: item for item in TARGET_CATALOG}


@dataclass(frozen=True)
class InstallPlan:
    target: str
    scope: str
    action: str
    destination: str | None
    command: list[str] | None
    completion: str
    note: str


def destination_for(
    target: str,
    scope: str,
    project_root: Path,
    generic_destination: Path | None = None,
) -> Path:
    home = Path.home()
    if target == "codex":
        base = home / ".agents" / "skills" if scope == "user" else project_root / ".agents" / "skills"
        return base / SKILL_NAME
    if target == "claude":
        base = home / ".claude" / "skills" if scope == "user" else project_root / ".claude" / "skills"
        return base / SKILL_NAME
    if target == "gemini":
        base = home / ".gemini" / "skills" if scope == "user" else project_root / ".gemini" / "skills"
        return base / SKILL_NAME
    if target == "copilot":
        base = home / ".copilot" / "skills" if scope == "user" else project_root / ".github" / "skills"
        return base / SKILL_NAME
    if target == "hermes":
        if scope != "user":
            raise ValueError("Hermes 首版只支持 user scope；请安装到 ~/.hermes/skills/productivity/")
        return home / ".hermes" / "skills" / "productivity" / SKILL_NAME
    if target == "generic":
        if generic_destination is None:
            raise ValueError("generic target 需要 --destination")
        return generic_destination.expanduser().resolve()
    raise ValueError(f"{target} 不使用直接复制安装")


def plan_for(
    target: str,
    scope: str,
    project_root: Path,
    generic_destination: Path | None = None,
) -> InstallPlan:
    if target in CATALOG_BY_TARGET and scope not in CATALOG_BY_TARGET[target]["scopes"]:
        supported = "|".join(CATALOG_BY_TARGET[target]["scopes"])
        raise ValueError(f"{target} 不支持 scope={scope}；可用范围: {supported}")
    if target in COPY_TARGETS:
        destination = destination_for(target, scope, project_root, generic_destination)
        return InstallPlan(
            target=target,
            scope=scope,
            action="copy",
            destination=str(destination),
            command=None,
            completion="installed-after-apply",
            note="拒绝覆盖已有目录；安装后按平台要求刷新会话。",
        )
    if target == "openclaw":
        command = ["openclaw", "skills", "install", str(ROOT), "--as", SKILL_NAME]
        if scope == "user":
            command.append("--global")
        return InstallPlan(
            target=target,
            scope=scope,
            action="command",
            destination=None,
            command=command,
            completion="installed-after-apply",
            note="使用 OpenClaw 官方本地目录安装；不会使用 .skill 压缩包。",
        )
    if target == "workbuddy":
        output = ROOT / "dist" / f"{SKILL_NAME}-{package_skill.VERSION}-workbuddy.zip"
        return InstallPlan(
            target=target,
            scope=scope,
            action="package-for-ui",
            destination=str(output),
            command=None,
            completion="manual-upload-required",
            note="本步骤只生成本地技能包，不代表安装完成；必须在 WorkBuddy 技能页面上传并验证。",
        )
    raise ValueError(f"不支持的 target: {target}")


def _copy_bundle(destination: Path, upgrade: bool = False) -> Path | None:
    backup: Path | None = None
    legacy_destination = destination.with_name(LEGACY_SKILL_NAME)
    if legacy_destination.exists() and not destination.exists():
        raise FileExistsError(
            f"检测到旧标识，拒绝并行安装: {legacy_destination}；请先报告路径并由用户决定迁移或删除。"
        )
    if destination.exists() or destination.is_symlink():
        if not upgrade:
            raise FileExistsError(f"目标已存在，未覆盖: {destination}")
        skill_file = destination / "SKILL.md"
        if not skill_file.is_file() or "name: reviewwrite" not in skill_file.read_text(
            encoding="utf-8"
        ):
            raise ValueError(f"目标不是可识别的 ReviewWrite，拒绝升级: {destination}")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = destination.parent / ".reviewwrite-backups"
        backup = backup_root / f"{destination.name}-{timestamp}"
        if backup.exists():
            raise FileExistsError(f"备份目标已存在: {backup}")
        backup_root.mkdir(parents=True, exist_ok=True)
        destination.rename(backup)
    try:
        destination.mkdir(parents=True)
        for source in package_skill.bundle_files():
            relative = source.relative_to(ROOT)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        if backup is not None:
            backup.rename(destination)
        raise
    return backup


def apply_plan(plan: InstallPlan, upgrade: bool = False) -> Path | None:
    if plan.action == "copy":
        assert plan.destination is not None
        return _copy_bundle(Path(plan.destination), upgrade=upgrade)
    if plan.action == "command":
        assert plan.command is not None
        subprocess.run(plan.command, cwd=ROOT, check=True)
        return None
    if plan.action == "package-for-ui":
        assert plan.destination is not None
        package_skill.build(Path(plan.destination))
        return None
    raise ValueError(f"未知安装动作: {plan.action}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="预览或安装 ReviewWrite 跨 Agent Skill")
    parser.add_argument(
        "--target",
        choices=(*ALL_TARGETS, "all", "generic"),
        help="当前 Agent 平台；省略时仅可配合 --list-targets 查询",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="列出当前安装器支持的平台标识，不执行安装",
    )
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--destination", type=Path, help="generic target 的安装目录")
    parser.add_argument("--apply", action="store_true", help="实际执行；默认只预览")
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="仅配合 --apply：验证旧副本后保留备份并升级；默认拒绝覆盖",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_targets:
        if args.format == "json":
            print(json.dumps(TARGET_CATALOG, ensure_ascii=False, indent=2))
        else:
            print("ReviewWrite installer targets:")
            for item in TARGET_CATALOG:
                scopes = "|".join(item["scopes"])
                print(
                    f"- {item['target']}: {item['platform']} "
                    f"(scope={scopes}; completion={item['completion']})"
                )
            print("generic 不参与自动选择；仅在用户明确提供 --destination 时使用。")
        return 0
    if args.target is None:
        parser.error("需要 --target；可先运行 --list-targets 查询支持的平台")

    targets = ALL_TARGETS if args.target == "all" else (args.target,)
    plans: list[InstallPlan] = []
    try:
        for target in targets:
            plans.append(
                plan_for(
                    target,
                    args.scope,
                    args.project_root.resolve(),
                    args.destination,
                )
            )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([asdict(plan) for plan in plans], ensure_ascii=False, indent=2))
    else:
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"ReviewWrite installer: {mode}")
        for plan in plans:
            detail = plan.destination or " ".join(plan.command or [])
            print(f"- {plan.target}: {plan.action} -> {detail}")
            print(f"  completion: {plan.completion}")
            print(f"  {plan.note}")

    if not args.apply:
        return 0

    if args.upgrade and any(plan.action != "copy" for plan in plans):
        print("--upgrade 仅适用于直接复制安装的平台", file=sys.stderr)
        return 2

    for plan in plans:
        try:
            backup = apply_plan(plan, upgrade=args.upgrade)
            if backup is not None:
                print(f"已保留旧版本备份: {backup}")
            if plan.completion == "manual-upload-required":
                print("尚未安装：请在 WorkBuddy 技能页面上传生成的包并完成发现验证。")
        except (FileExistsError, OSError, ValueError, subprocess.CalledProcessError) as exc:
            print(f"安装失败 [{plan.target}]: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
