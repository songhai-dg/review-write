#!/usr/bin/env python3
"""Extract and strictly validate a ReviewWrite deliverable before release."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import reviewwrite_lint
from runtime_io import configure_utf8_stdio


def gate_response(
    text: str,
    *,
    input_mode: str = "structured",
    profiles: Sequence[str] = (),
    confirm_context_warnings: bool = False,
) -> dict[str, object]:
    """Return a body only when extraction and strict linting both pass."""
    if input_mode not in {"structured", "raw"}:
        raise ValueError("input_mode 必须为 structured 或 raw")
    try:
        body = (
            reviewwrite_lint.extract_surface(text, "deliverable_body")
            if input_mode == "structured"
            else text
        )
    except reviewwrite_lint.ProtocolError as exc:
        return {
            "status": "blocked",
            "stage": "extract",
            "body": None,
            "findings": [],
            "message": str(exc),
        }

    if not body.strip():
        return {
            "status": "blocked",
            "stage": "extract",
            "body": None,
            "findings": [],
            "message": "交付正文为空",
        }

    findings = reviewwrite_lint.lint_text(body, profiles=profiles)
    blocking_findings = [
        finding
        for finding in findings
        if not (confirm_context_warnings and finding.applied_profile)
    ]
    if reviewwrite_lint.exit_code_for(blocking_findings, strict=True):
        return {
            "status": "blocked",
            "stage": "strict-lint",
            "body": None,
            "findings": [asdict(item) for item in blocking_findings],
            "message": "正文未通过严格终检",
        }
    return {
        "status": "passed",
        "stage": "deliver",
        "body": body,
        "findings": [],
        "confirmed_context_findings": [
            asdict(item) for item in findings if item.applied_profile
        ],
        "message": "正文已通过结构化抽取与严格终检",
    }


def _read(path_value: str) -> tuple[str, str]:
    if path_value == "-":
        return sys.stdin.read(), "<stdin>"
    path = Path(path_value)
    try:
        return path.read_text(encoding="utf-8"), str(path)
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"无法读取 {path}: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="抽取 ReviewWrite 正文，严格终检后只输出可交付正文。"
    )
    parser.add_argument("path", help="UTF-8 响应文件；使用 - 从 stdin 读取")
    parser.add_argument(
        "--input-mode",
        choices=("structured", "raw"),
        default="structured",
        help="默认要求 deliverable_body 标签；仅正文输入必须显式选择 raw",
    )
    parser.add_argument("--genre", choices=sorted(reviewwrite_lint.GENRE_PROFILES))
    parser.add_argument(
        "--context",
        action="append",
        default=[],
        choices=sorted(reviewwrite_lint.CONTEXT_PROFILES),
    )
    parser.add_argument(
        "--confirm-context-warnings",
        action="store_true",
        help="显式确认已声明语境中的降级警告；不放行普通警告或硬失败",
    )
    parser.add_argument("--format", choices=("body", "json"), default="body")
    args = parser.parse_args(argv)
    profiles = ([args.genre] if args.genre else []) + list(args.context)
    if args.confirm_context_warnings and not args.context:
        parser.error("--confirm-context-warnings 必须与至少一个 --context 同时使用")
    try:
        source_text, source = _read(args.path)
        result = gate_response(
            source_text,
            input_mode=args.input_mode,
            profiles=profiles,
            confirm_context_warnings=args.confirm_context_warnings,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        payload = {**result, "source": source, "profiles": profiles}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif result["status"] == "passed":
        print(str(result["body"]))
    else:
        print(f"ReviewWrite gate blocked: {result['message']}", file=sys.stderr)
        for item in result["findings"]:
            print(
                f"{str(item['severity']).upper()} {item['rule_id']} "
                f"L{item['line']}:C{item['column']} {item['excerpt']}",
                file=sys.stderr,
            )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
