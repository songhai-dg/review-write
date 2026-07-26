from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PilotContractTests(unittest.TestCase):
    def test_pilot_contract_has_bounded_rounds_and_reviews(self) -> None:
        config = json.loads(
            (ROOT / "automation" / "pilot-20.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["total_rounds"], 20)
        self.assertEqual(config["review_rounds"], [4, 8, 12, 16, 20])
        self.assertEqual(config["max_action_rounds_per_day"], 2)
        self.assertEqual(config["candidate_branch"], "bot/pilot-20")
        self.assertEqual(
            config["pull_request_mode"], "one-draft-per-review-window"
        )
        policy = config["publication_policy"]
        self.assertTrue(policy["review_round_may_merge_main"])
        self.assertTrue(policy["review_round_may_create_stable_release"])
        self.assertFalse(policy["ordinary_round_may_publish"])
        self.assertFalse(policy["direct_push_main"])
        self.assertTrue(policy["require_pull_request"])
        self.assertTrue(policy["require_green_ci"])
        self.assertTrue(policy["require_reproducible_package"])

    def test_initial_state_matches_contract_and_current_version(self) -> None:
        state = json.loads(
            (ROOT / "automation" / "pilot-state.json").read_text(encoding="utf-8")
        )
        release = json.loads(
            (ROOT / "release-policy.json").read_text(encoding="utf-8")
        )
        self.assertEqual(state["pilot_id"], "reviewwrite-pilot-20")
        self.assertEqual(state["completed_rounds"], 0)
        self.assertEqual(state["current_version"], release["current_version"])

    def test_prompt_keeps_one_branch_and_review_only_release_gate(self) -> None:
        prompt = (ROOT / "automation" / "pilot-20.md").read_text(encoding="utf-8")
        self.assertIn("bot/pilot-20", prompt)
        self.assertIn("一次 Scheduled 运行最多完成一轮", prompt)
        self.assertIn("每个 Review 窗口最多维护一个 Draft PR", prompt)
        self.assertIn("禁止直接 push `main`", prompt)
        self.assertIn("Review 发布时增加 stable minor", prompt)


if __name__ == "__main__":
    unittest.main()
