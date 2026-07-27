#!/usr/bin/env python3
"""Chunked preflight for long ReviewWrite documents.

This is a deterministic preflight layer, not a semantic or citation checker.
It keeps the existing linter for short texts and adds chunk-local findings,
global line locations, protected-number indexing, ASCII term-variant checks,
and duplicate-paragraph signals for documents too large for one prompt pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import reviewwrite_lint


DEFAULT_MAX_CHARS = 12000
DEFAULT_OVERLAP = 256
NUMBER_PATTERN = re.compile(
    r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?:\s*[%％]|\s*[万亿千万])?(?![\w.])"
)
ASCII_TERM_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]{2,40}\b")
HEADING_PATTERN = re.compile(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$")


@dataclass(frozen=True)
class Chunk:
    index: int
    start: int
    end: int
    context_start: int
    context_end: int


def _excerpt(text: str, offset: int, limit: int = 180) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end < 0:
        end = len(text)
    value = " ".join(text[start:end].strip().split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    previous = text.rfind("\n", 0, offset)
    return line, offset + 1 if previous < 0 else offset - previous


def split_chunks(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Split at paragraph/line boundaries and add bounded context overlap."""
    if max_chars < 1000:
        raise ValueError("max_chars 必须至少为 1000")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap 必须大于等于 0 且小于 max_chars")
    if not text:
        return [Chunk(1, 0, 0, 0, 0)]

    chunks: list[Chunk] = []
    start = 0
    index = 1
    length = len(text)
    while start < length:
        target = min(start + max_chars, length)
        end = target
        if target < length:
            paragraph_break = text.rfind("\n\n", start, target)
            if paragraph_break > start + max_chars // 3:
                end = paragraph_break + 2
            else:
                line_break = text.rfind("\n", start, target)
                if line_break > start:
                    end = line_break + 1
        if end <= start:
            end = target
        context_start = max(0, start - overlap)
        context_end = min(length, end + overlap)
        chunks.append(Chunk(index, start, end, context_start, context_end))
        start = end
        index += 1
    return chunks


def _local_offset(text: str, line: int, column: int) -> int:
    if line <= 1:
        return max(0, column - 1)
    lines = text.splitlines(keepends=True)
    return sum(len(item) for item in lines[: line - 1]) + max(0, column - 1)


def _global_findings(
    full_text: str,
    chunk: Chunk,
    chunk_text: str,
    profiles: Iterable[str],
    ignored_rules: Iterable[str],
) -> list[dict[str, object]]:
    findings = reviewwrite_lint.lint_text(
        chunk_text,
        ignored_rules=ignored_rules,
        profiles=profiles,
    )
    output: list[dict[str, object]] = []
    for finding in findings:
        local_offset = _local_offset(chunk_text, finding.line, finding.column)
        global_offset = chunk.context_start + local_offset
        if not chunk.start <= global_offset < chunk.end:
            continue
        line, column = _line_column(full_text, global_offset)
        item = asdict(finding)
        item.update(
            {
                "chunk": chunk.index,
                "line": line,
                "column": column,
                "excerpt": _excerpt(full_text, global_offset),
            }
        )
        output.append(item)
    return output


def _number_index(text: str) -> list[dict[str, object]]:
    index: dict[str, dict[str, object]] = {}
    for match in NUMBER_PATTERN.finditer(text):
        value = match.group(0).strip()
        line, column = _line_column(text, match.start())
        entry = index.setdefault(value, {"value": value, "count": 0, "locations": []})
        entry["count"] = int(entry["count"]) + 1
        locations = entry["locations"]
        assert isinstance(locations, list)
        if len(locations) < 20:
            locations.append({"line": line, "column": column})
    return sorted(index.values(), key=lambda item: str(item["value"]))


def _term_variants(text: str) -> list[dict[str, object]]:
    variants: dict[str, set[str]] = defaultdict(set)
    locations: dict[str, list[dict[str, int]]] = defaultdict(list)
    for match in ASCII_TERM_PATTERN.finditer(text):
        value = match.group(0)
        key = value.lower()
        variants[key].add(value)
        if len(locations[key]) < 10:
            line, column = _line_column(text, match.start())
            locations[key].append({"line": line, "column": column})
    return [
        {"key": key, "variants": sorted(values), "locations": locations[key]}
        for key, values in sorted(variants.items())
        if len(values) > 1
    ]


def _duplicate_paragraphs(text: str) -> list[dict[str, object]]:
    groups: dict[str, list[tuple[int, str]]] = defaultdict(list)
    cursor = 0
    for paragraph in re.split(r"\n\s*\n", text):
        normalized = " ".join(paragraph.split())
        position = text.find(paragraph, cursor)
        if position < 0:
            position = cursor
        cursor = position + len(paragraph)
        if len(normalized) < 40:
            continue
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        line = text.count("\n", 0, position) + 1
        groups[digest].append((line, normalized[:120]))
    return [
        {"occurrences": occurrences}
        for occurrences in groups.values()
        if len(occurrences) > 1
    ]


def review_document(
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
    profiles: Iterable[str] = (),
    ignored_rules: Iterable[str] = (),
) -> dict[str, object]:
    chunks = split_chunks(text, max_chars=max_chars, overlap=overlap)
    findings: list[dict[str, object]] = []
    for chunk in chunks:
        chunk_text = text[chunk.context_start : chunk.context_end]
        findings.extend(
            _global_findings(text, chunk, chunk_text, profiles, ignored_rules)
        )
    deduped: dict[tuple[object, object, object], dict[str, object]] = {}
    for finding in findings:
        key = (finding["rule_id"], finding["line"], finding["column"])
        deduped[key] = finding
    findings = sorted(
        deduped.values(),
        key=lambda item: (int(item["line"]), int(item["column"]), str(item["rule_id"])),
    )
    headings = [
        {"title": match.group(1).strip(), "line": _line_column(text, match.start())[0]}
        for match in HEADING_PATTERN.finditer(text)
    ]
    fail_count = sum(item["severity"] == "fail" for item in findings)
    warn_count = sum(item["severity"] == "warn" for item in findings)
    return {
        "summary": {
            "characters": len(text),
            "lines": text.count("\n") + (1 if text else 0),
            "chunks": len(chunks),
            "max_chars": max_chars,
            "overlap": overlap,
            "fail": fail_count,
            "warn": warn_count,
        },
        "headings": headings,
        "number_index": _number_index(text),
        "term_variants": _term_variants(text),
        "duplicate_paragraphs": _duplicate_paragraphs(text),
        "findings": findings,
        "limitations": [
            "分块预检不能替代主张—证据、引用、法律和学术专业复核。",
            "块之间使用有限上下文重叠；跨段语义关系仍需模型或人工全局复核。",
            "数字索引、术语变体和重复段落是复核线索，不是事实错误判定。",
        ],
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
    parser = argparse.ArgumentParser(
        description="对超长 ReviewWrite 文档进行分块预检和全局一致性索引。"
    )
    parser.add_argument("path", help="UTF-8 文本文件；使用 - 从 stdin 读取")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--ignore-rule", action="append", default=[])
    parser.add_argument("--genre", choices=sorted(reviewwrite_lint.GENRE_PROFILES))
    parser.add_argument("--context", action="append", choices=sorted(reviewwrite_lint.CONTEXT_PROFILES), default=[])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    profiles = ([args.genre] if args.genre else []) + list(args.context)
    try:
        text, source = _read(args.path)
        result = review_document(
            text,
            max_chars=args.max_chars,
            overlap=args.overlap,
            profiles=profiles,
            ignored_rules=args.ignore_rule,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result["source"] = source
    result["profiles"] = profiles
    fail_count = int(result["summary"]["fail"])
    warn_count = int(result["summary"]["warn"])
    code = 1 if fail_count or (args.strict and warn_count) else 0
    result["status"] = "fail" if code else "pass"
    result["strict"] = args.strict
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result["summary"]
        print(
            f"ReviewWrite long-document preflight: {source}\n"
            f"{summary['characters']} chars, {summary['lines']} lines, "
            f"{summary['chunks']} chunks; {summary['fail']} fail, {summary['warn']} warn"
        )
        for item in result["findings"]:
            print(
                f"{item['severity'].upper()} {item['rule_id']} "
                f"L{item['line']}:C{item['column']} "
                f"(chunk {item['chunk']}) {item['excerpt']}"
            )
        print(
            f"global indexes: {len(result['headings'])} headings, "
            f"{len(result['number_index'])} numbers, "
            f"{len(result['term_variants'])} term variants, "
            f"{len(result['duplicate_paragraphs'])} duplicate groups"
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
