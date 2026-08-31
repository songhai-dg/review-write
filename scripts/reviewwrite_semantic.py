#!/usr/bin/env python3
"""Create and validate a body-bound ReviewWrite semantic review record."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

import reviewwrite_lint
from runtime_io import configure_utf8_stdio


SCHEMA_VERSION = 1
CHECKS = (
    "title_structure_reader_facing",
    "instruction_process_separated",
    "self_certification_removed",
    "claims_evidence_bounded",
    "facts_qualifiers_preserved",
)
ACCEPTED_STATUSES = {"passed", "not_applicable"}


def body_sha256(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def review_template(body: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "body_sha256": body_sha256(body),
        "checks": {name: "pending" for name in CHECKS},
        "notes": {},
    }


def validate_review(body: str, payload: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 必须为 {SCHEMA_VERSION}")
    expected_hash = body_sha256(body)
    if payload.get("body_sha256") != expected_hash:
        errors.append("语义复核记录与当前正文哈希不一致；正文变化后必须重新复核")
    checks = payload.get("checks")
    if not isinstance(checks, Mapping):
        errors.append("checks 必须是对象")
        return errors
    notes = payload.get("notes", {})
    if not isinstance(notes, Mapping):
        errors.append("notes 必须是对象")
        notes = {}
    for name in CHECKS:
        status = checks.get(name)
        if status not in ACCEPTED_STATUSES:
            errors.append(f"{name} 必须明确为 passed 或 not_applicable")
        if status == "not_applicable" and not str(notes.get(name, "")).strip():
            errors.append(f"{name} 标记 not_applicable 时必须说明理由")
    unknown = sorted(set(checks) - set(CHECKS))
    if unknown:
        errors.append(f"存在未知检查项: {', '.join(unknown)}")
    return errors


def _read_body(path: Path, input_mode: str) -> str:
    text = path.read_text(encoding="utf-8")
    if input_mode == "raw":
        return text
    return reviewwrite_lint.extract_surface(text, "deliverable_body")


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="创建或校验与正文哈希绑定的语义复核记录")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="创建 pending 状态的复核模板")
    init_parser.add_argument("body", type=Path)
    init_parser.add_argument("--input-mode", choices=("structured", "raw"), default="structured")
    init_parser.add_argument("--output", type=Path, required=True)

    check_parser = subparsers.add_parser("check", help="校验复核记录及正文哈希")
    check_parser.add_argument("body", type=Path)
    check_parser.add_argument("review", type=Path)
    check_parser.add_argument("--input-mode", choices=("structured", "raw"), default="structured")
    check_parser.add_argument("--format", choices=("text", "json"), default="text")

    args = parser.parse_args(argv)
    try:
        body = _read_body(args.body, args.input_mode)
        if args.command == "init":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(review_template(body), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(args.output)
            return 0
        payload = json.loads(args.review.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, reviewwrite_lint.ProtocolError) as exc:
        parser.error(str(exc))

    errors = validate_review(body, payload)
    result = {"status": "passed" if not errors else "blocked", "errors": errors}
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        for error in errors:
            print(error)
    else:
        print("语义复核记录有效")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
