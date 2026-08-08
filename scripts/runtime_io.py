#!/usr/bin/env python3
"""Small cross-platform text I/O helpers for ReviewWrite command-line tools."""

from __future__ import annotations

import sys
from typing import TextIO


def _reconfigure(stream: TextIO) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def configure_utf8_stdio() -> None:
    """Make redirected and Windows CLI text deterministic UTF-8."""
    _reconfigure(sys.stdin)
    _reconfigure(sys.stdout)
    _reconfigure(sys.stderr)
