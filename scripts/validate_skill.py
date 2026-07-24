#!/usr/bin/env python3
"""Validate the ReviewWrite skill bundle without third-party dependencies."""

from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "SKILL.md",
    "skills/reviewwrite/SKILL.md",
    "README.md",
    "LICENSE",
    "NOTICE.md",
    "SECURITY.md",
    "INSTALL_PROMPT.md",
    "sources.lock.json",
    "compatibility.json",
    "release-policy.json",
    "agents/openai.yaml",
    "references/ontology.md",
    "references/review-rubric.md",
    "references/leakage.md",
    "references/few-shot-policy.md",
    "references/style-signals.md",
    "references/language-packs/README.md",
    "references/language-packs/zh-CN.md",
    "references/language-packs/en.md",
    "references/platforms.md",
    "references/update-policy.md",
    "references/quickstart.md",
    "references/office-qa.md",
    "references/font-profiles.md",
    "references/office-integrations.md",
    "examples/office-qa/font-profile.example.json",
    "references/fewshots/manifest.json",
    "examples/simulation/manifest.json",
    "examples/simulation/RUN_REPORT.md",
    "scripts/reviewwrite_lint.py",
    "scripts/reviewwrite_update.py",
    "scripts/print_install_prompt.py",
    "scripts/render_release_notes.py",
    "scripts/office_qa.py",
)


def validate() -> list[str]:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"缺少文件: {relative}")

    skill_path = ROOT / "SKILL.md"
    if skill_path.is_file():
        skill_text = skill_path.read_text(encoding="utf-8")
        if not skill_text.startswith("---\n"):
            errors.append("SKILL.md 缺少 YAML frontmatter")
        for required_line in (
            "name: reviewwrite",
        ):
            if required_line not in skill_text:
                errors.append(f"SKILL.md 缺少元数据: {required_line}")

    readme_path = ROOT / "README.md"
    if readme_path.is_file():
        readme = readme_path.read_text(encoding="utf-8")
        for heading in ("## 中文", "## English"):
            if heading not in readme:
                errors.append(f"README.md 缺少双语章节: {heading}")

        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill_text):
            if target.startswith(("http://", "https://", "#")):
                continue
            if not (ROOT / target).exists():
                errors.append(f"SKILL.md 链接不存在: {target}")

    try:
        import print_install_prompt

        canonical_prompt = print_install_prompt.render(
            print_install_prompt.repository(None)
        )
        for document in (
            "README.md",
            "INSTALL_PROMPT.md",
            "references/platforms.md",
        ):
            if canonical_prompt not in (ROOT / document).read_text(encoding="utf-8"):
                errors.append(f"安装提示与生成器不一致: {document}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"安装提示无效: {exc}")

    runtime_skill_path = ROOT / "skills" / "reviewwrite" / "SKILL.md"
    if runtime_skill_path.is_file() and skill_path.is_file():
        runtime_version = re.search(
            r"(?m)^version: ([^\n]+)$", runtime_skill_path.read_text(encoding="utf-8")
        )
        root_version = re.search(
            r"(?m)^version: ([^\n]+)$", skill_path.read_text(encoding="utf-8")
        )
        if not runtime_version or not root_version or runtime_version.group(1) != root_version.group(1):
            errors.append("根目录与运行时 SKILL.md 版本不一致")

        if "natural_language_aliases: [\"审写\", \"ReviewWrite\"]" not in skill_text:
            errors.append("SKILL.md 缺少审写与 ReviewWrite 的自然语言简称声明")

        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme):
            if target.startswith(("http://", "https://", "#")):
                continue
            if not (ROOT / target).exists():
                errors.append(f"README.md 链接不存在: {target}")

    genre_dir = ROOT / "references" / "genre-packs"
    genre_files = sorted(genre_dir.glob("*.md")) if genre_dir.is_dir() else []
    if len(genre_files) < 10:
        errors.append(f"体裁包不足 10 个，当前 {len(genre_files)} 个")

    manifest_path = ROOT / "references" / "fewshots" / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"few-shot manifest 无效: {exc}")
        else:
            seen_ids: set[str] = set()
            for item in manifest.get("examples", []):
                example_id = item.get("id")
                if not example_id:
                    errors.append("few-shot 条目缺少 id")
                elif example_id in seen_ids:
                    errors.append(f"few-shot id 重复: {example_id}")
                else:
                    seen_ids.add(example_id)
                for required_key in (
                    "language",
                    "locale",
                    "discourse_community",
                    "genres",
                    "issue_tags",
                    "protected_features",
                    "source",
                    "license",
                ):
                    if not item.get(required_key):
                        errors.append(f"few-shot 条目缺少 {required_key}: {example_id}")
                path_value = item.get("path")
                example_path = manifest_path.parent / str(path_value or "")
                if not path_value or not example_path.is_file():
                    errors.append(f"few-shot 文件不存在: {path_value}")
                    continue
                example_text = example_path.read_text(encoding="utf-8")
                if f"id: {example_id}" not in example_text:
                    errors.append(f"few-shot 文件 id 不匹配: {path_value}")
                for heading in ("## Before", "## After", "## Why", "## Do not copy"):
                    if heading not in example_text:
                        errors.append(f"few-shot 缺少 {heading}: {path_value}")

    sources_path = ROOT / "sources.lock.json"
    if sources_path.is_file():
        try:
            sources = json.loads(sources_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"sources.lock.json 无效: {exc}")
        else:
            for source in sources.get("sources", []):
                commit = source.get("commit")
                if commit is not None and not re.fullmatch(r"[0-9a-f]{40}", commit):
                    errors.append(f"上游 commit 不是完整 SHA: {source.get('name')}")
                if not source.get("license"):
                    errors.append(f"上游缺少 license: {source.get('name')}")

    try:
        compatibility = json.loads((ROOT / "compatibility.json").read_text(encoding="utf-8"))
        release_policy = json.loads((ROOT / "release-policy.json").read_text(encoding="utf-8"))
        skill_version = re.search(
            r"(?m)^version: ([^\n]+)$",
            (ROOT / "SKILL.md").read_text(encoding="utf-8"),
        ).group(1)
        versions = {
            skill_version,
            str(compatibility["reviewwrite_version"]),
            str(release_policy["current_version"]),
        }
        if len(versions) != 1:
            errors.append(f"版本字段不一致: {sorted(versions)}")
        required_platforms = {
            "codex",
            "claude-code",
            "hermes-agent",
            "gemini-cli",
            "github-copilot",
            "openclaw",
            "workbuddy",
        }
        missing_platforms = required_platforms - set(compatibility.get("platforms", {}))
        if missing_platforms:
            errors.append(f"缺少平台兼容声明: {sorted(missing_platforms)}")
        core_languages = set(compatibility.get("language_support", {}).get("core", []))
        if not {"zh-CN", "en"} <= core_languages:
            errors.append("核心语言声明必须包含 zh-CN 和 en")
        office_qa = compatibility.get("office_qa", {})
        if office_qa.get("status") != "audit-only":
            errors.append("Office QA 必须保持 audit-only 默认边界")
        if set(office_qa.get("formats", [])) != {"docx", "pptx"}:
            errors.append("Office QA 格式声明必须为 docx 与 pptx")
        if compatibility.get("skill_id") != "reviewwrite":
            errors.append("技术 Skill ID 必须为 reviewwrite")
        if set(compatibility.get("natural_language_aliases", [])) != {"审写", "ReviewWrite"}:
            errors.append("自然语言简称必须为 审写 与 ReviewWrite")
        manifest = json.loads(
            (ROOT / "references" / "fewshots" / "manifest.json").read_text(encoding="utf-8")
        )
        if manifest.get("selection_limit") != 3:
            errors.append("few-shot selection_limit 必须为 3")
        expected_layers = {"risk-repair", "genre-locale-calibration", "author-voice"}
        if set(manifest.get("selection_layers", [])) != expected_layers:
            errors.append("few-shot 三层路由声明不完整")
        font_profile = json.loads(
            (ROOT / "examples" / "office-qa" / "font-profile.example.json").read_text(
                encoding="utf-8"
            )
        )
        if not font_profile.get("name") or not isinstance(font_profile.get("fonts"), dict):
            errors.append("Office QA 字体 profile 示例无效")
    except (AttributeError, KeyError, OSError, json.JSONDecodeError) as exc:
        errors.append(f"兼容/发布配置无效: {exc}")

    for script_name in (
        "scripts/reviewwrite_lint.py",
        "scripts/validate_skill.py",
        "scripts/package_skill.py",
        "scripts/install_skill.py",
        "scripts/reviewwrite_update.py",
        "scripts/bump_version.py",
        "scripts/print_install_prompt.py",
        "scripts/render_release_notes.py",
        "scripts/office_qa.py",
    ):
        script_path = ROOT / script_name
        if script_path.is_file():
            try:
                py_compile.compile(str(script_path), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"Python 语法错误 {script_name}: {exc.msg}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"Validation failed: {len(errors)} issue(s)")
        return 1
    print("Validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
