import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_distribution_kit


class DistributionKitTests(unittest.TestCase):
    def test_kit_has_one_canonical_source_and_expected_adapters(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "kit"
            build_distribution_kit.files("0.5.2", output)
            manifest = json.loads((output / "distribution-manifest.json").read_text())
            self.assertEqual(manifest["canonical_source"], "https://github.com/songhai-dg/review-write")
            self.assertEqual(manifest["mirror_source"], "https://gitee.com/cufe01/songhai-dg")
            for name in (
                "install-prompt.txt",
                "github-release.md",
                "skillhub-update.md",
                "agent-directory.md",
                "wechat-and-video.md",
            ):
                self.assertTrue((output / name).is_file(), name)

    def test_install_prompt_does_not_guess_platform_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "kit"
            build_distribution_kit.files("0.5.2", output)
            prompt = (output / "install-prompt.txt").read_text()
            self.assertIn("平台自己的 Skill 安装或导入机制", prompt)
            self.assertNotIn(".hermes", prompt)
            self.assertNotIn("Path.home", prompt)


if __name__ == "__main__":
    unittest.main()
