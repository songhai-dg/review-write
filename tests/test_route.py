from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import package_skill  # noqa: E402
import reviewwrite_route  # noqa: E402


class ReviewWriteRouteTests(unittest.TestCase):
    def test_high_risk_formal_genre_is_required(self):
        decision = reviewwrite_route.route(task_type="rewrite", genre="research-report")
        self.assertEqual(decision["invoke"], "required")
        self.assertEqual(decision["final_gate"], "required")

    def test_long_document_is_high_risk(self):
        self.assertEqual(reviewwrite_route.route(task_type="summarize", characters=100_000)["tier"], "high")

    def test_formal_task_without_genre_is_suggested(self):
        decision = reviewwrite_route.route(task_type="rewrite")
        self.assertEqual(decision["tier"], "medium")
        self.assertEqual(decision["final_gate"], "required-if-invoked")

    def test_ordinary_chat_is_not_intercepted(self):
        self.assertEqual(reviewwrite_route.route(task_type="chat")["invoke"], "not-needed")

    def test_office_audit_is_required_when_explicitly_requested(self):
        decision = reviewwrite_route.route(task_type="office-audit")
        self.assertEqual(decision["invoke"], "required")
        self.assertEqual(decision["final_gate"], "office-qa-required")

    def test_bilingual_professional_writing_is_high_risk(self):
        decision = reviewwrite_route.route(task_type="translate", language="bilingual")
        self.assertEqual(decision["tier"], "high")
        self.assertEqual(decision["invoke"], "required")

    def test_explicit_skip_is_never_reported_as_reviewed(self):
        decision = reviewwrite_route.route(task_type="write", explicit_skip=True)
        self.assertIn("不得声称", decision["warning"])

    def test_route_is_bundled(self):
        paths = {path.relative_to(ROOT).as_posix() for path in package_skill.bundle_files()}
        self.assertIn("scripts/reviewwrite_route.py", paths)
        self.assertIn("scripts/reviewwrite_gate.py", paths)


if __name__ == "__main__":
    unittest.main()
