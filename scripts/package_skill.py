#!/usr/bin/env python3
"""Build a deterministic runtime-only ReviewWrite .skill archive."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.6.0"
SKILL_ID = "reviewwrite"


def bundle_files() -> list[Path]:
    explicit = [
        ROOT / "SKILL.md",
        ROOT / "agents" / "openai.yaml",
        ROOT / "scripts" / "reviewwrite_lint.py",
        ROOT / "scripts" / "office_qa.py",
        ROOT / "examples" / "office-qa" / "font-profile.example.json",
    ]
    references = sorted(path for path in (ROOT / "references").rglob("*") if path.is_file())
    return sorted(explicit + references, key=lambda path: path.relative_to(ROOT).as_posix())


def build(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in bundle_files():
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 7, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建 ReviewWrite .skill 文件")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / f"{SKILL_ID}-{VERSION}.skill",
    )
    args = parser.parse_args(argv)
    output = build(args.output.resolve())
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
