from __future__ import annotations

import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reviewwrite_semantic  # noqa: E402


class SemanticReviewTests(unittest.TestCase):
    def test_template_starts_pending_and_is_body_bound(self):
        payload = reviewwrite_semantic.review_template("正文。")
        self.assertEqual(set(payload["checks"]), set(reviewwrite_semantic.CHECKS))
        self.assertEqual(set(payload["checks"].values()), {"pending"})
        self.assertTrue(reviewwrite_semantic.validate_review("正文。", payload))

    def test_completed_review_passes(self):
        payload = reviewwrite_semantic.review_template("正文。")
        payload["checks"] = {name: "passed" for name in reviewwrite_semantic.CHECKS}
        self.assertEqual(reviewwrite_semantic.validate_review("正文。", payload), [])

    def test_not_applicable_requires_reason(self):
        payload = reviewwrite_semantic.review_template("正文。")
        payload["checks"] = {name: "passed" for name in reviewwrite_semantic.CHECKS}
        payload["checks"]["facts_qualifiers_preserved"] = "not_applicable"
        errors = reviewwrite_semantic.validate_review("正文。", payload)
        self.assertTrue(any("必须说明理由" in error for error in errors))
        payload["notes"] = {"facts_qualifiers_preserved": "任务为原创写作，没有待改写源文。"}
        self.assertEqual(reviewwrite_semantic.validate_review("正文。", payload), [])


if __name__ == "__main__":
    unittest.main()
