from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reviewwrite_gate  # noqa: E402


class ReviewWriteGateTests(unittest.TestCase):
    def test_clean_structured_response_returns_body_without_tags(self):
        result = reviewwrite_gate.gate_response(
            "<deliverable_body>样本覆盖186家企业，结论仅适用于本次调查。</deliverable_body>"
        )
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["body"], "样本覆盖186家企业，结论仅适用于本次调查。")

    def test_internal_term_in_body_is_blocked(self):
        result = reviewwrite_gate.gate_response(
            "<deliverable_body>本报告已经通过最终门禁。</deliverable_body>"
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["body"])
        self.assertEqual(result["stage"], "strict-lint")

    def test_text_outside_structured_envelope_is_blocked(self):
        result = reviewwrite_gate.gate_response(
            "这是修改结果。<deliverable_body>可交付正文。</deliverable_body>"
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stage"], "extract")

    def test_raw_body_requires_explicit_mode(self):
        self.assertEqual(
            reviewwrite_gate.gate_response("可交付正文。")["status"], "blocked"
        )
        self.assertEqual(
            reviewwrite_gate.gate_response("调查覆盖186家企业。", input_mode="raw")["status"],
            "passed",
        )

    def test_cli_emits_no_body_when_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "response.txt"
            path.write_text(
                "<deliverable_body>总的来说，这个结论很重要。</deliverable_body>",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/reviewwrite_gate.py"), str(path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("RW-W-217", result.stderr)

    def test_context_warning_requires_explicit_confirmation(self):
        text = "<deliverable_body>本文讨论 system prompt 注入。</deliverable_body>"
        blocked = reviewwrite_gate.gate_response(text, profiles=["ai-safety"])
        passed = reviewwrite_gate.gate_response(
            text,
            profiles=["ai-safety"],
            confirm_context_warnings=True,
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(passed["status"], "passed")
        self.assertEqual(
            passed["confirmed_context_findings"][0]["applied_profile"], "ai-safety"
        )

    def test_context_confirmation_never_allows_ordinary_style_warnings(self):
        result = reviewwrite_gate.gate_response(
            "<deliverable_body>总的来说，这项工作很重要。</deliverable_body>",
            profiles=["ai-safety"],
            confirm_context_warnings=True,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("RW-W-217", {item["rule_id"] for item in result["findings"]})


if __name__ == "__main__":
    unittest.main()
