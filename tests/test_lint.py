from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reviewwrite_lint  # noqa: E402
import package_skill  # noqa: E402
import install_skill  # noqa: E402
import bump_version  # noqa: E402
import reviewwrite_update  # noqa: E402
import print_install_prompt  # noqa: E402
import render_release_notes  # noqa: E402
import office_qa  # noqa: E402


class ReviewWriteLintTests(unittest.TestCase):
    def test_clean_policy_has_no_findings(self) -> None:
        text = (ROOT / "tests/fixtures/clean_policy.zh.md").read_text(encoding="utf-8")
        self.assertEqual(reviewwrite_lint.lint_text(text), [])

    def test_leaky_text_has_hard_failures_and_warnings(self) -> None:
        text = (ROOT / "tests/fixtures/leaky.zh.md").read_text(encoding="utf-8")
        findings = reviewwrite_lint.lint_text(text)
        rule_ids = {item.rule_id for item in findings}
        self.assertTrue({"RW-F-002", "RW-F-003", "RW-F-004", "RW-F-005"} <= rule_ids)
        self.assertIn("RW-W-103", rule_ids)
        self.assertEqual(reviewwrite_lint.exit_code_for(findings), 1)

    def test_warning_only_passes_unless_strict(self) -> None:
        findings = reviewwrite_lint.lint_text("本节将介绍研究方法。")
        self.assertTrue(findings)
        self.assertEqual(reviewwrite_lint.exit_code_for(findings), 0)
        self.assertEqual(reviewwrite_lint.exit_code_for(findings, strict=True), 1)

    def test_abstract_intensifier_is_a_review_signal_not_a_hard_failure(self) -> None:
        findings = reviewwrite_lint.lint_text("这项技术真正改变了行业未来。")
        self.assertIn("RW-W-207", {item.rule_id for item in findings})
        self.assertEqual(reviewwrite_lint.exit_code_for(findings), 0)

    def test_formulaic_bridges_are_contextual_review_signals(self) -> None:
        draft = (
            "换句话说，答案很可能不是效率。"
            "这件事最吸引人的地方在于，它看上去更完整。"
            "这也是最危险的地方：遗漏期限的摘要同样会显得完整。"
        )
        findings = reviewwrite_lint.lint_text(draft)
        self.assertEqual(
            {item.rule_id for item in findings}, {"RW-W-208"}
        )
        self.assertEqual(reviewwrite_lint.exit_code_for(findings), 0)
        revised = "评估重点不应是摘要速度，而应是是否保留退款期限。"
        self.assertEqual(reviewwrite_lint.lint_text(revised), [])

    def test_technical_commentary_detects_stacked_signals(self) -> None:
        draft = (
            "这是一个 34.66B 参数的稀疏 MoE 模型，每个 token 激活约 3B 参数。"
            "这个细节很关键，端侧推理真正卡住的不是参数总量，而是每次生成 token 要搬多少权重。"
            "这比单次跑分更重要，因为大多数用户并不关心模型听起来有多大，"
            "他们关心电脑能不能跑、手机能不能装。端侧 AI 未必从旗舰 GPU 普及，"
            "而更可能从内存够、软件通、模型拆得聪明的设备开始。"
        )
        findings = reviewwrite_lint.lint_text(
            draft, profiles=["technical-commentary"]
        )
        rule_ids = {item.rule_id for item in findings}
        self.assertTrue(
            {
                "RW-W-209",
                "RW-W-210",
                "RW-W-211",
                "RW-W-212",
            } <= rule_ids
        )
        self.assertEqual(reviewwrite_lint.exit_code_for(findings), 0)

    def test_one_technical_contrast_is_not_a_composite_signal(self) -> None:
        text = "端侧推理关注的不是文件大小，而是目标设备上的内存带宽。"
        findings = reviewwrite_lint.lint_text(
            text, profiles=["technical-commentary"]
        )
        self.assertNotIn("RW-W-209", {item.rule_id for item in findings})
        self.assertNotIn("RW-W-210", {item.rule_id for item in findings})

    def test_repeated_sentence_initial_enumeration_is_a_contextual_signal(self) -> None:
        draft = (
            "第一，模型要足够小。\n"
            "第二，工具链要足够稳定。\n"
            "第三，设备还要有足够的内存。"
        )
        findings = reviewwrite_lint.lint_text(draft, profiles=["public-article"])
        self.assertIn("RW-W-213", {item.rule_id for item in findings})
        self.assertEqual(reviewwrite_lint.exit_code_for(findings), 0)

    def test_formal_document_profile_does_not_trigger_enumeration_signal(self) -> None:
        draft = "第一，明确责任主体。\n第二，规定办理时限。\n第三，保留例外情形。"
        findings = reviewwrite_lint.lint_text(
            draft, profiles=["official-document"]
        )
        self.assertNotIn("RW-W-213", {item.rule_id for item in findings})

    def test_simulation_inputs_fail_and_outputs_pass_without_fact_loss(self) -> None:
        simulation_root = ROOT / "examples" / "simulation"
        manifest = json.loads(
            (simulation_root / "manifest.json").read_text(encoding="utf-8")
        )
        for sample in manifest["samples"]:
            with self.subTest(sample=sample["id"]):
                before = (simulation_root / sample["input"]).read_text(encoding="utf-8")
                after = (simulation_root / sample["output"]).read_text(encoding="utf-8")
                before_findings = reviewwrite_lint.lint_text(before)
                after_findings = reviewwrite_lint.lint_text(after)
                self.assertGreaterEqual(
                    sum(item.severity == "fail" for item in before_findings),
                    sample["minimum_input_failures"],
                )
                self.assertGreaterEqual(
                    sum(item.severity == "warn" for item in before_findings),
                    sample["minimum_input_warnings"],
                )
                self.assertEqual(after_findings, [])
                for literal in sample["protected_literals"]:
                    self.assertIn(literal, before)
                    self.assertIn(literal, after)

    def test_ai_safety_context_downgrades_hard_leakage_to_warn(self) -> None:
        text = "本文分析 system prompt 注入的防御方法。"
        baseline = reviewwrite_lint.lint_text(text)
        self.assertEqual(
            [item.severity for item in baseline if item.rule_id == "RW-F-001"],
            ["fail"],
        )
        self.assertEqual(reviewwrite_lint.exit_code_for(baseline), 1)

        exempted = reviewwrite_lint.lint_text(text, profiles=["ai-safety"])
        finding = next(item for item in exempted if item.rule_id == "RW-F-001")
        self.assertEqual(finding.severity, "warn")
        self.assertEqual(finding.original_severity, "fail")
        self.assertEqual(finding.applied_profile, "ai-safety")
        self.assertEqual(reviewwrite_lint.exit_code_for(exempted), 0)

    def test_unrelated_profile_does_not_relax_leakage(self) -> None:
        text = "本文分析 system prompt 注入的防御方法。"
        findings = reviewwrite_lint.lint_text(text, profiles=["official-document"])
        finding = next(item for item in findings if item.rule_id == "RW-F-001")
        self.assertEqual(finding.severity, "fail")
        self.assertEqual(reviewwrite_lint.exit_code_for(findings), 1)

    def test_genre_ignores_functional_formatting_warning(self) -> None:
        text = "- **背景**：说明\n- **目标**：达成\n"
        baseline_ids = {item.rule_id for item in reviewwrite_lint.lint_text(text)}
        self.assertIn("RW-W-205", baseline_ids)
        exempted = reviewwrite_lint.lint_text(text, profiles=["official-document"])
        self.assertNotIn("RW-W-205", {item.rule_id for item in exempted})

    def test_ignore_outranks_downgrade_for_same_rule(self) -> None:
        # editorial-audit downgrades RW-F-001; dialogue-transcript also downgrades it.
        # RW-W-103 is ignored by dialogue-transcript regardless of other profiles.
        text = "希望这对你有帮助。"
        findings = reviewwrite_lint.lint_text(
            text, profiles=["dialogue-transcript", "ai-safety"]
        )
        self.assertNotIn("RW-W-103", {item.rule_id for item in findings})

    def test_cli_context_flag_downgrades_and_reports_profiles(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/reviewwrite_lint.py"),
                "-",
                "--context",
                "ai-safety",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            input="本文分析 system prompt 注入的防御方法。\n",
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["profiles"], ["ai-safety"])
        finding = next(f for f in payload["findings"] if f["rule_id"] == "RW-F-001")
        self.assertEqual(finding["severity"], "warn")
        self.assertEqual(finding["applied_profile"], "ai-safety")

    def test_cli_rejects_unknown_profile(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/reviewwrite_lint.py"),
                "-",
                "--context",
                "not-a-real-context",
            ],
            check=False,
            capture_output=True,
            text=True,
            input="x\n",
        )
        self.assertEqual(result.returncode, 2)

    def test_cli_list_profiles_needs_no_path(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/reviewwrite_lint.py"),
                "--list-profiles",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ai-safety", result.stdout)
        self.assertIn("official-document", result.stdout)

    def test_every_exemption_targets_a_real_rule(self) -> None:
        rule_ids = {rule.rule_id for rule in reviewwrite_lint.RULES}
        for exemption in reviewwrite_lint.EXEMPTIONS:
            self.assertIn(exemption.rule_id, rule_ids)
            self.assertIn(exemption.action, {"ignore", "downgrade"})
            self.assertIn(
                exemption.profile,
                reviewwrite_lint.ALL_PROFILES,
            )

    def test_ignore_rule(self) -> None:
        findings = reviewwrite_lint.lint_text(
            "本节将介绍研究方法。", ignored_rules=["RW-W-101"]
        )
        self.assertEqual(findings, [])

    def test_structured_surfaces_keep_review_evidence_out_of_body_lint(self) -> None:
        response = """<review_report>
根据用户提供的提示词，原文包含模型身份说明。
</review_report>
<revision_plan>保留数字，删除过程泄漏。</revision_plan>
<deliverable_body>
本研究报告显示，样本内结果仍需进一步核验。
</deliverable_body>
<verification_report>正文未发现泄漏；数字和限定条件已逐项核对。</verification_report>"""
        surfaces = reviewwrite_lint.parse_surfaces(response)
        self.assertIn("提示词", surfaces["review_report"])
        self.assertEqual(
            reviewwrite_lint.lint_text(surfaces["deliverable_body"]), []
        )
        with self.assertRaises(reviewwrite_lint.ProtocolError):
            reviewwrite_lint.extract_surface(
                response + "\n如果你需要，我可以继续。", "deliverable_body"
            )

    def test_named_surface_requires_structured_boundary(self) -> None:
        with self.assertRaises(reviewwrite_lint.ProtocolError):
            reviewwrite_lint.extract_surface("只有正文，没有标签。", "deliverable_body")

    def test_cli_json_output(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/reviewwrite_lint.py"),
                str(ROOT / "tests/fixtures/leaky.zh.md"),
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertGreaterEqual(payload["summary"]["fail"], 4)

    def test_skill_bundle_contains_runtime_and_references(self) -> None:
        import tempfile
        import zipfile

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reviewwrite.skill"
            package_skill.build(output)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("SKILL.md", names)
            self.assertNotIn("skills/reviewwrite/SKILL.md", names)
            self.assertIn("scripts/reviewwrite_lint.py", names)
            self.assertIn("scripts/office_qa.py", names)
            self.assertIn("references/leakage.md", names)
            self.assertIn("references/office-qa.md", names)
            self.assertIn("references/quickstart.md", names)
            self.assertIn("examples/office-qa/font-profile.example.json", names)
            self.assertIn("references/fewshots/manifest.json", names)
            self.assertIn("agents/openai.yaml", names)
            self.assertIn("references/language-packs/README.md", names)
            self.assertNotIn("scripts/reviewwrite_update.py", names)
            self.assertNotIn("scripts/install_skill.py", names)
            self.assertNotIn("tests/test_lint.py", names)

    def test_docx_office_qa_detects_profile_mismatch_without_claiming_availability(self) -> None:
        import tempfile
        import zipfile

        document_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p>
  <w:r><w:rPr><w:rFonts w:eastAsia=\"Wrong Chinese\"/></w:rPr><w:t>中文正文</w:t></w:r>
  <w:r><w:rPr><w:rFonts w:ascii=\"Confirmed Latin Body Font\"/></w:rPr><w:t>English body</w:t></w:r>
</w:p></w:body></w:document>"""
        profile = {
            "name": "test-profile",
            "fonts": {
                "eastAsia": ["Confirmed Chinese Body Font"],
                "latin": ["Confirmed Latin Body Font"],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docx = root / "sample.docx"
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            profile_path = root / "profile.json"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
            report = office_qa.audit(docx, profile_path=profile_path)
        self.assertEqual(report["status"], "warning")
        self.assertEqual(report["availability_inventory"], "not_checked")
        self.assertEqual(report["render_gate"]["status"], "skipped")
        self.assertIn("Wrong Chinese", report["audit"]["direct_font_usage"]["eastAsia"])
        self.assertIn("RW-O-101", {item["code"] for item in report["audit"]["findings"]})

    def test_pptx_office_qa_checks_east_asia_run_and_render_requirement(self) -> None:
        import tempfile
        import zipfile

        theme_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<a:theme xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\"><a:themeElements><a:fontScheme>
  <a:majorFont><a:latin typeface=\"Major Latin\"/><a:ea typeface=\"Major Chinese\"/></a:majorFont>
  <a:minorFont><a:latin typeface=\"Confirmed Latin Body Font\"/><a:ea typeface=\"Confirmed Chinese Body Font\"/></a:minorFont>
</a:fontScheme></a:themeElements></a:theme>"""
        slide_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<p:sld xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\" xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\">
<p:cSld><p:spTree><p:sp><p:txBody><a:p>
  <a:r><a:rPr><a:ea typeface=\"Wrong Chinese\"/></a:rPr><a:t>中文标题</a:t></a:r>
  <a:r><a:rPr><a:latin typeface=\"Confirmed Latin Body Font\"/></a:rPr><a:t>English title</a:t></a:r>
</a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"""
        profile = {
            "name": "test-profile",
            "fonts": {
                "eastAsia": ["Confirmed Chinese Body Font"],
                "latin": ["Confirmed Latin Body Font"],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pptx = root / "sample.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/theme/theme1.xml", theme_xml)
                archive.writestr("ppt/slides/slide1.xml", slide_xml)
            profile_path = root / "profile.json"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
            normal = office_qa.audit(pptx, profile_path=profile_path, render="off")
            with mock.patch("office_qa.shutil.which", return_value=None):
                required = office_qa.audit(pptx, profile_path=profile_path, render="required")
        self.assertIn("RW-O-201", {item["code"] for item in normal["audit"]["findings"]})
        self.assertEqual(required["status"], "blocker")
        self.assertEqual(required["render_gate"]["status"], "unavailable")
        self.assertIn("RW-O-401", {item["code"] for item in required["audit"]["findings"]})

    def test_cross_platform_install_plans_are_non_destructive(self) -> None:
        project_root = ROOT / "tests" / "fixtures"
        codex = install_skill.plan_for("codex", "project", project_root)
        claude = install_skill.plan_for("claude", "user", project_root)
        hermes = install_skill.plan_for("hermes", "user", project_root)
        gemini = install_skill.plan_for("gemini", "user", project_root)
        copilot = install_skill.plan_for("copilot", "project", project_root)
        openclaw = install_skill.plan_for("openclaw", "user", project_root)
        workbuddy = install_skill.plan_for("workbuddy", "user", project_root)

        self.assertTrue(codex.destination.endswith(".agents/skills/reviewwrite"))
        self.assertTrue(claude.destination.endswith(".claude/skills/reviewwrite"))
        self.assertTrue(hermes.destination.endswith(".hermes/skills/productivity/reviewwrite"))
        self.assertTrue(gemini.destination.endswith(".gemini/skills/reviewwrite"))
        self.assertTrue(copilot.destination.endswith(".github/skills/reviewwrite"))
        self.assertIn("--global", openclaw.command or [])
        self.assertEqual(openclaw.completion, "installed-after-apply")
        self.assertEqual(workbuddy.action, "package-for-ui")
        self.assertEqual(workbuddy.completion, "manual-upload-required")
        self.assertTrue((workbuddy.destination or "").endswith("-workbuddy.zip"))
        self.assertNotIn("--force", openclaw.command or [])

    def test_copy_targets_apply_inside_an_isolated_home(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            isolated_home = Path(directory)
            with mock.patch("install_skill.Path.home", return_value=isolated_home):
                for target in ("codex", "claude", "hermes", "gemini", "copilot"):
                    plan = install_skill.plan_for(target, "user", ROOT)
                    self.assertIsNone(install_skill.apply_plan(plan))
                    assert plan.destination is not None
                    self.assertTrue((Path(plan.destination) / "SKILL.md").is_file())

    def test_unsupported_scope_is_rejected_before_apply(self) -> None:
        with self.assertRaisesRegex(ValueError, "不支持 scope=project"):
            install_skill.plan_for("workbuddy", "project", ROOT)

    def test_installer_lists_targets_without_requiring_a_target(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/install_skill.py"),
                "--list-targets",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        catalog = json.loads(result.stdout)
        self.assertEqual(
            [item["target"] for item in catalog], list(install_skill.ALL_TARGETS)
        )
        self.assertNotIn("generic", [item["target"] for item in catalog])
        workbuddy = next(item for item in catalog if item["target"] == "workbuddy")
        self.assertEqual(workbuddy["completion"], "manual-upload-required")

    def test_update_policy_never_auto_installs_major(self) -> None:
        current = reviewwrite_update.Version.parse("1.2.3")
        self.assertTrue(
            reviewwrite_update.policy_allows(
                current, reviewwrite_update.Version.parse("1.2.4"), "auto-patch"
            )
        )
        self.assertFalse(
            reviewwrite_update.policy_allows(
                current, reviewwrite_update.Version.parse("1.3.0"), "auto-patch"
            )
        )
        self.assertTrue(
            reviewwrite_update.policy_allows(
                current, reviewwrite_update.Version.parse("1.3.0"), "auto-minor"
            )
        )
        self.assertFalse(
            reviewwrite_update.policy_allows(
                current, reviewwrite_update.Version.parse("2.0.0"), "auto-minor"
            )
        )

    def test_copy_upgrade_preserves_previous_bundle(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills" / "reviewwrite"
            self.assertIsNone(install_skill._copy_bundle(destination))
            backup = install_skill._copy_bundle(destination, upgrade=True)
            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertTrue((backup / "SKILL.md").is_file())
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_version_fields_are_synchronized(self) -> None:
        self.assertEqual(str(bump_version.synchronized_current()), package_skill.VERSION)
        self.assertEqual(
            bump_version.next_version(reviewwrite_update.Version.parse("0.1.1"), "minor"),
            reviewwrite_update.Version.parse("0.2.0"),
        )

    def test_install_prompt_uses_official_https_repository(self) -> None:
        prompt = print_install_prompt.render("ecoaitech/review-write")
        self.assertIn("https://github.com/ecoaitech/review-write", prompt)
        self.assertIn("安装 ReviewWrite Skill", prompt)
        self.assertIn("已经安装，不要重复安装", prompt)
        self.assertIn("所在平台自己的 Skill 安装或导入机制", prompt)
        self.assertIn("当前目录", prompt)
        self.assertNotIn("启用", prompt)
        self.assertNotIn("--target TARGET", prompt)
        self.assertNotIn("<OFFICIAL_REPOSITORY_URL>", prompt)

    def test_official_install_prompt_offers_gitee_fallback_without_platform_details(self) -> None:
        prompt = print_install_prompt.render("songhai-dg/review-write")
        self.assertIn("https://github.com/songhai-dg/review-write", prompt)
        self.assertIn("不要搜索或替换成名称相近的其他技能", prompt)
        self.assertIn("所在平台自己的 Skill 安装或导入机制", prompt)
        self.assertIn("https://gitee.com/cufe01/songhai-dg", prompt)
        self.assertNotIn("SHA-256", prompt)
        self.assertNotIn("Release", prompt)

    def test_legacy_skill_directory_is_not_installed_in_parallel(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills" / "reviewwrite"
            legacy = destination.with_name("review-write")
            legacy.mkdir(parents=True)
            with self.assertRaisesRegex(FileExistsError, "旧标识"):
                install_skill._copy_bundle(destination)

    def test_install_prompt_is_consistent_across_public_documents(self) -> None:
        prompt = print_install_prompt.render(print_install_prompt.repository(None))
        for document in (
            "README.md",
            "INSTALL_PROMPT.md",
            "references/platforms.md",
        ):
            self.assertIn(prompt, (ROOT / document).read_text(encoding="utf-8"))

    def test_release_notes_are_versioned_and_actionable(self) -> None:
        notes = render_release_notes.render("0.2.0")
        self.assertIn("# 审写 · ReviewWrite v0.2.0", notes)
        self.assertIn("## 本版更新", notes)
        self.assertIn("## 安装与安全", notes)
        self.assertIn("SHA-256", notes)
        self.assertIn("--context", notes)


if __name__ == "__main__":
    unittest.main()
