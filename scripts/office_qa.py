#!/usr/bin/env python3
"""Read-only DOCX/PPTX typography audit for ReviewWrite.

The tool intentionally does not edit Office files.  It reports direct OOXML
font assignments, theme references, profile mismatches, and the state of an
optional render gate.  A successful structural audit is not proof that a
recipient machine has every font or that a rendered page is visually clean.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"w": W_NS, "a": A_NS}
W_VAL = f"{{{W_NS}}}val"

CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
LATIN_RE = re.compile(r"[A-Za-z]")


class OfficeQaError(ValueError):
    """The supplied document or configuration cannot be audited."""


def read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(archive.read(name))
    except KeyError:
        return None
    except ET.ParseError as exc:
        raise OfficeQaError(f"OOXML 无法解析: {name}: {exc}") from exc


def element_text(element: ET.Element) -> str:
    return "".join(element.itertext()).strip()


def script_for(text: str) -> str | None:
    if CJK_RE.search(text):
        return "eastAsia"
    if LATIN_RE.search(text):
        return "latin"
    return None


def normalize_font(value: str | None) -> str | None:
    if not value or value.startswith("+"):
        return None
    return value.strip() or None


def theme_fonts(root: ET.Element | None) -> dict[str, str]:
    if root is None:
        return {}
    result: dict[str, str] = {}
    scheme = root.find(".//a:fontScheme", NS)
    if scheme is None:
        return result
    for family, prefix in (("majorFont", "mj"), ("minorFont", "mn")):
        node = scheme.find(f"a:{family}", NS)
        if node is None:
            continue
        for child, suffix in (("latin", "lt"), ("ea", "ea"), ("cs", "cs")):
            value = node.find(f"a:{child}", NS)
            if value is not None and value.get("typeface"):
                result[f"+{prefix}-{suffix}"] = value.get("typeface", "")
    return result


def parse_profile(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"name": "unconfigured", "fonts": {}}
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OfficeQaError(f"字体配置无效: {exc}") from exc
    if not isinstance(profile, dict) or not isinstance(profile.get("name"), str):
        raise OfficeQaError("字体配置必须是包含 name 的 JSON 对象")
    if "fonts" in profile and not isinstance(profile["fonts"], dict):
        raise OfficeQaError("字体配置 fonts 必须是对象")
    return profile


def wanted_fonts(profile: dict[str, Any], office_kind: str, script: str) -> set[str]:
    fonts: dict[str, Any] = {}
    common = profile.get("fonts", {})
    if isinstance(common, dict):
        fonts.update(common)
    scoped = profile.get(office_kind, {})
    if isinstance(scoped, dict) and isinstance(scoped.get("fonts"), dict):
        fonts.update(scoped["fonts"])
    values = fonts.get(script, [])
    if isinstance(values, str):
        values = [values]
    return {value for value in values if isinstance(value, str) and value.strip()}


def direct_docx_fonts(run: ET.Element) -> dict[str, str]:
    fonts = run.find("w:rPr/w:rFonts", NS)
    if fonts is None:
        return {}
    mapping = {
        "ascii": "latin",
        "hAnsi": "latin",
        "eastAsia": "eastAsia",
        "cs": "complex",
    }
    result: dict[str, str] = {}
    for attr, script in mapping.items():
        value = fonts.get(f"{{{W_NS}}}{attr}")
        if value:
            result[script] = value
    return result


def finding(
    code: str, severity: str, location: str, message: str, font: str | None = None
) -> dict[str, str]:
    item = {"code": code, "severity": severity, "location": location, "message": message}
    if font:
        item["font"] = font
    return item


def audit_docx(path: Path, profile: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    direct_usage: dict[str, Counter[str]] = defaultdict(Counter)
    unresolved: Counter[str] = Counter()
    with zipfile.ZipFile(path) as archive:
        document = read_xml(archive, "word/document.xml")
        if document is None:
            raise OfficeQaError("不是可识别的 DOCX：缺少 word/document.xml")
        theme = theme_fonts(read_xml(archive, "word/theme/theme1.xml"))
        run_count = 0
        for index, run in enumerate(document.findall(".//w:r", NS), start=1):
            text = element_text(run)
            if not text:
                continue
            run_count += 1
            script = script_for(text)
            fonts = direct_docx_fonts(run)
            location = f"word/document.xml:run-{index}"
            if script is None:
                continue
            expected = wanted_fonts(profile, "docx", script)
            actual = fonts.get(script)
            if actual:
                direct_usage[script][actual] += 1
                if expected and actual not in expected:
                    findings.append(
                        finding(
                            "RW-O-101",
                            "warn",
                            location,
                            f"直接设置的 {script} 字体不符合当前 profile。",
                            actual,
                        )
                    )
            else:
                unresolved[script] += 1
                if script == "eastAsia":
                    findings.append(
                        finding(
                            "RW-O-102",
                            "info",
                            location,
                            "含中文的 run 未直接设置 eastAsia 字体；需结合样式、模板和渲染结果确认继承字体。",
                        )
                    )
        if run_count == 0:
            findings.append(finding("RW-O-103", "warn", "word/document.xml", "未找到可审计的文本 run。"))
    return {
        "office_kind": "docx",
        "theme_fonts": theme,
        "direct_font_usage": {key: dict(value) for key, value in direct_usage.items()},
        "unresolved_inheritance": dict(unresolved),
        "findings": findings,
    }


def iter_ppt_runs(slide: ET.Element) -> Iterable[tuple[str, dict[str, str]]]:
    for run in slide.findall(".//a:r", NS) + slide.findall(".//a:fld", NS):
        text_node = run.find("a:t", NS)
        text = text_node.text if text_node is not None and text_node.text else ""
        props = run.find("a:rPr", NS)
        fonts: dict[str, str] = {}
        if props is not None:
            for child, script in (("latin", "latin"), ("ea", "eastAsia"), ("cs", "complex")):
                font_node = props.find(f"a:{child}", NS)
                if font_node is not None and font_node.get("typeface"):
                    fonts[script] = font_node.get("typeface", "")
            # Some producers use the run-level typeface attribute rather than
            # child font nodes. It is a useful fallback, not proof of script-specific intent.
            if props.get("typeface") and "latin" not in fonts:
                fonts["latin"] = props.get("typeface", "")
        yield text, fonts


def resolve_theme_font(value: str, theme: dict[str, str], script: str) -> str | None:
    if value == "+mn-ea" and theme.get("+mn-ea"):
        return theme["+mn-ea"]
    if value == "+mj-ea" and theme.get("+mj-ea"):
        return theme["+mj-ea"]
    if value in {"+mn-lt", "+mj-lt"}:
        return theme.get(value)
    return normalize_font(value)


def audit_pptx(path: Path, profile: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    direct_usage: dict[str, Counter[str]] = defaultdict(Counter)
    unresolved: Counter[str] = Counter()
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=lambda name: int(re.search(r"slide(\d+)", name).group(1)),
        )
        if not slide_names:
            raise OfficeQaError("不是可识别的 PPTX：未找到 ppt/slides/slideN.xml")
        theme = theme_fonts(read_xml(archive, "ppt/theme/theme1.xml"))
        for slide_name in slide_names:
            slide = read_xml(archive, slide_name)
            if slide is None:
                continue
            for run_index, (text, fonts) in enumerate(iter_ppt_runs(slide), start=1):
                if not text:
                    continue
                script = script_for(text)
                if script is None:
                    continue
                location = f"{slide_name}:run-{run_index}"
                typeface = fonts.get(script) or fonts.get("latin")
                actual = resolve_theme_font(typeface, theme, script) if typeface else None
                expected = wanted_fonts(profile, "pptx", script)
                if actual:
                    direct_usage[script][actual] += 1
                    if expected and actual not in expected:
                        findings.append(
                            finding(
                                "RW-O-201",
                                "warn",
                                location,
                                f"直接设置的 {script} 字体不符合当前 profile。",
                                actual,
                            )
                        )
                else:
                    unresolved[script] += 1
                    if script == "eastAsia":
                        findings.append(
                            finding(
                                "RW-O-202",
                                "info",
                                location,
                                "含中文的 run 未直接设置或无法解析东亚字体；需检查母版、主题和渲染结果。",
                            )
                        )
    return {
        "office_kind": "pptx",
        "theme_fonts": theme,
        "direct_font_usage": {key: dict(value) for key, value in direct_usage.items()},
        "unresolved_inheritance": dict(unresolved),
        "findings": findings,
    }


def read_available_fonts(path: Path | None) -> set[str] | None:
    if path is None:
        return None
    try:
        if path.suffix.lower() == ".json":
            values = json.loads(path.read_text(encoding="utf-8"))
        else:
            values = path.read_text(encoding="utf-8").splitlines()
    except (OSError, json.JSONDecodeError) as exc:
        raise OfficeQaError(f"可用字体清单无效: {exc}") from exc
    if not isinstance(values, list):
        raise OfficeQaError("可用字体清单必须是 JSON 数组或每行一个字体名称的文本")
    return {item.strip() for item in values if isinstance(item, str) and item.strip()}


def availability_findings(
    audit: dict[str, Any], available_fonts: set[str] | None
) -> list[dict[str, str]]:
    if available_fonts is None:
        return []
    findings: list[dict[str, str]] = []
    all_used = {
        font
        for fonts in audit["direct_font_usage"].values()
        for font in fonts
    }
    for font in sorted(all_used - available_fonts):
        findings.append(
            finding(
                "RW-O-301",
                "warn",
                "target-font-inventory",
                "目标环境字体清单中不存在此字体；可能发生替代或版式变化。",
                font,
            )
        )
    return findings


def render_gate(path: Path, mode: str, output_dir: Path | None) -> dict[str, Any]:
    if mode == "off":
        return {"status": "skipped", "reason": "render disabled by caller"}
    soffice = shutil.which("soffice")
    if not soffice:
        return {"status": "unavailable", "reason": "soffice not found; structural audit only"}
    destination = output_dir or Path(tempfile.mkdtemp(prefix="reviewwrite-office-qa-"))
    destination.mkdir(parents=True, exist_ok=True)
    command = [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(destination), str(path)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    pdf_path = destination / f"{path.stem}.pdf"
    if completed.returncode != 0 or not pdf_path.is_file():
        return {
            "status": "failed",
            "reason": "soffice conversion failed",
            "stderr": completed.stderr[-1000:],
        }
    pngs: list[str] = []
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        prefix = destination / path.stem
        raster = subprocess.run(
            [pdftoppm, "-png", "-r", "144", str(pdf_path), str(prefix)],
            capture_output=True,
            text=True,
            check=False,
        )
        if raster.returncode == 0:
            pngs = [str(item) for item in sorted(destination.glob(f"{path.stem}-*.png"))]
    return {
        "status": "rendered_pending_inspection",
        "pdf": str(pdf_path),
        "pngs": pngs,
        "instruction": "必须逐页查看渲染图，确认无缺字、字体回退、溢出、截断或异常换行后，才能通过视觉门禁。",
    }


def audit(
    path: Path,
    profile_path: Path | None = None,
    available_fonts_path: Path | None = None,
    render: str = "off",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    if not path.is_file():
        raise OfficeQaError(f"文件不存在: {path}")
    suffix = path.suffix.lower()
    if suffix not in {".docx", ".pptx"}:
        raise OfficeQaError("仅支持 .docx 和 .pptx")
    if not zipfile.is_zipfile(path):
        raise OfficeQaError("Office Open XML 文件必须是 ZIP 容器")
    profile = parse_profile(profile_path)
    available_fonts = read_available_fonts(available_fonts_path)
    office_audit = audit_docx(path, profile) if suffix == ".docx" else audit_pptx(path, profile)
    office_audit["findings"].extend(availability_findings(office_audit, available_fonts))
    gate = render_gate(path, render, output_dir)
    if render == "required" and gate["status"] != "rendered_pending_inspection":
        office_audit["findings"].append(
            finding("RW-O-401", "blocker", "render-gate", "要求渲染验证，但渲染门禁未完成。")
        )
    severities = Counter(item["severity"] for item in office_audit["findings"])
    status = "blocker" if severities["blocker"] else "warning" if severities["warn"] else "pass"
    return {
        "tool": "reviewwrite-office-qa",
        "tool_version": "0.3.0",
        "input": str(path.resolve()),
        "profile": profile["name"],
        "availability_inventory": "checked" if available_fonts is not None else "not_checked",
        "status": status,
        "summary": {"blocker": severities["blocker"], "warn": severities["warn"], "info": severities["info"]},
        "audit": office_audit,
        "render_gate": gate,
        "repair_policy": "audit-only; do not modify the original file. A separate, explicitly authorized repair workflow must write a new file and re-run this audit.",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ReviewWrite DOCX/PPTX 字体与渲染审计（只读）")
    parser.add_argument("input", type=Path, help="待审计的 .docx 或 .pptx")
    parser.add_argument("--font-profile", type=Path, help="经确认的字体 profile JSON")
    parser.add_argument("--available-fonts", type=Path, help="目标环境字体清单（JSON 数组或每行一个字体）")
    parser.add_argument("--render", choices=("auto", "required", "off"), default="off")
    parser.add_argument("--output-dir", type=Path, help="渲染产物目录；不写入输入文件目录")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)
    try:
        report = audit(
            args.input,
            profile_path=args.font_profile,
            available_fonts_path=args.available_fonts,
            render=args.render,
            output_dir=args.output_dir,
        )
    except OfficeQaError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status']}: {report['input']}")
        print(json.dumps(report["summary"], ensure_ascii=False))
        print(f"render: {report['render_gate']['status']}")
    return 1 if report["status"] == "blocker" else 0


if __name__ == "__main__":
    raise SystemExit(main())
