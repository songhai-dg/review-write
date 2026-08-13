#!/usr/bin/env python3
"""Read-only provenance and delivery-integrity audit for ReviewWrite.

This module deliberately does not remove, rewrite, or claim to defeat provenance
signals.  It reports observable markers and uncertainty so a host can preserve
source information and make an appropriate disclosure decision.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from runtime_io import configure_utf8_stdio


SUSPICIOUS_FORMAT_CONTROLS = {
    "\u061c": "arabic-letter-mark",
    "\u200b": "zero-width-space",
    "\u200c": "zero-width-non-joiner",
    "\u200d": "zero-width-joiner",
    "\u200e": "left-to-right-mark",
    "\u200f": "right-to-left-mark",
    "\u202a": "left-to-right-embedding",
    "\u202b": "right-to-left-embedding",
    "\u202c": "pop-directional-formatting",
    "\u202d": "left-to-right-override",
    "\u202e": "right-to-left-override",
    "\u2060": "word-joiner",
    "\u2066": "left-to-right-isolate",
    "\u2067": "right-to-left-isolate",
    "\u2068": "first-strong-isolate",
    "\u2069": "pop-directional-isolate",
    "\ufeff": "zero-width-no-break-space",
}

SOURCE_MARKERS = (
    (b"c2pa", "c2pa-content-credentials", "metadata-or-container-marker"),
    (b"jumbf", "jumbf-content-credentials-container", "container-marker"),
    (b"synthid", "synthid-reference", "metadata-or-documentary-reference"),
)


@dataclass(frozen=True)
class AuditFinding:
    code: str
    severity: str
    subject: str
    message: str
    positions: tuple[int, ...] = ()


def _format_controls(text: str) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for character, label in SUSPICIOUS_FORMAT_CONTROLS.items():
        positions = tuple(index for index, value in enumerate(text) if value == character)
        if positions:
            findings.append(
                AuditFinding(
                    code="RW-P-W-001",
                    severity="warn",
                    subject="unicode-format-control",
                    message=(
                        f"发现 {len(positions)} 个 Unicode 格式控制字符（{label}）；"
                        "先确认其确有语言、方向或排版用途，不要在未确认前删除。"
                    ),
                    positions=positions[:20],
                )
            )
    return findings


def audit_text(text: str) -> dict[str, object]:
    """Audit text without attempting text-watermark detection or mutation."""

    findings = _format_controls(text)
    return {
        "status": "completed",
        "input_kind": "text",
        "source_provenance": {
            "status": "cannot_determine",
            "reason": "当前没有把文本模型判别或文本水印推断冒充来源证据。",
        },
        "observable_signals": [],
        "findings": [asdict(item) for item in findings],
        "preservation": {
            "mutated": False,
            "source_markers_removed": False,
            "note": "审计只读；未检测到可观察信号也不等于来源信号不存在。",
        },
    }


def _scan_bytes(data: bytes, *, documentary_only: bool = False) -> list[dict[str, str]]:
    lowered = data.lower()
    signals: list[dict[str, str]] = []
    for marker, name, kind in SOURCE_MARKERS:
        if marker in lowered:
            signals.append(
                {
                    "name": name,
                    "status": "reference_found" if documentary_only else "detected",
                    "basis": "documentary-text-reference" if documentary_only else kind,
                    "note": (
                        "仅表示正文或文档中提到该技术名称，不等于文件含有对应来源信号。"
                        if documentary_only
                        else "仅表示文件中发现可观察标记，不等于完成来源归属认证。"
                    ),
                }
            )
    return signals


def audit_file(path: Path) -> dict[str, object]:
    """Audit a file's observable provenance markers and embedded text controls."""

    data = path.read_bytes()
    documentary_only = path.suffix.lower() in {
        ".txt",
        ".md",
        ".markdown",
        ".csv",
        ".json",
        ".xml",
        ".html",
        ".docx",
    }
    signals = _scan_bytes(data, documentary_only=documentary_only)
    findings: list[AuditFinding] = []
    if not signals:
        findings.append(
            AuditFinding(
                code="RW-P-I-001",
                severity="info",
                subject="provenance-unknown",
                message="未发现本工具支持的可观察来源标记；不能据此断定文件没有来源信息。",
            )
        )

    text_parts: list[str] = []
    if path.suffix.lower() in {".txt", ".md", ".markdown", ".csv", ".json", ".xml", ".html"}:
        text_parts.append(data.decode("utf-8", errors="replace"))
    elif path.suffix.lower() == ".docx":
        try:
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if name.endswith(".xml"):
                        text_parts.append(archive.read(name).decode("utf-8", errors="replace"))
        except zipfile.BadZipFile:
            findings.append(
                AuditFinding(
                    code="RW-P-F-001",
                    severity="fail",
                    subject="invalid-office-container",
                    message="文件扩展名为 DOCX，但容器无法读取；未完成完整审计。",
                )
            )
    for part in text_parts:
        findings.extend(_format_controls(part))

    return {
        "status": "completed" if not any(item.severity == "fail" for item in findings) else "incomplete",
        "input_kind": "file",
        "path": str(path),
        "size_bytes": len(data),
        "source_provenance": {
            "status": (
                "reference_found"
                if signals and documentary_only
                else "signal_detected"
                if signals
                else "cannot_determine"
            ),
            "reason": (
                "文件中发现可观察来源标记，但仍需平台或签名方验证。"
                if signals and not documentary_only
                else "文本或文档中的技术名称只是文字引用，不代表文件含有对应来源信号。"
                if signals
                else "未发现本工具支持的可观察标记，不能据此断定来源信息不存在。"
            ),
        },
        "observable_signals": signals,
        "findings": [asdict(item) for item in findings],
        "preservation": {
            "mutated": False,
            "source_markers_removed": False,
            "note": "审计只读；没有删除元数据、内容凭证或不可见字符。",
        },
    }


def _text_report(result: dict[str, object]) -> str:
    lines = [f"状态：{result['status']}", f"输入类型：{result['input_kind']}"]
    provenance = result["source_provenance"]
    assert isinstance(provenance, dict)
    lines.append(f"来源状态：{provenance['status']}（{provenance['reason']}）")
    signals = result["observable_signals"]
    assert isinstance(signals, list)
    lines.append(f"可观察来源信号：{len(signals)} 项")
    findings = result["findings"]
    assert isinstance(findings, list)
    for finding in findings:
        lines.append(f"- {finding['code']} [{finding['severity']}] {finding['message']}")
    lines.append("完整性：只读审计，未修改输入，未移除来源标记。")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ReviewWrite 来源与交付完整性只读审计")
    parser.add_argument("path", nargs="?", type=Path, help="待审计文件；不提供时从标准输入读取文本")
    parser.add_argument("--text", help="直接审计一段文本；不能与 path 同时使用")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.text is not None and args.path is not None:
        parser.error("--text 不能与 path 同时使用")
    if args.text is not None:
        result = audit_text(args.text)
    elif args.path is not None:
        if not args.path.is_file():
            parser.error(f"文件不存在或不可读: {args.path}")
        result = audit_file(args.path)
    else:
        result = audit_text(sys.stdin.read())
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_text_report(result))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
