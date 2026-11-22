from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reviewwrite_provenance  # noqa: E402


class ProvenanceAuditTests(unittest.TestCase):
    def test_text_audit_is_read_only_and_does_not_claim_text_watermark_absence(self):
        text = "正文\u200b内容"
        result = reviewwrite_provenance.audit_text(text)
        self.assertFalse(result["preservation"]["mutated"])
        self.assertEqual(result["source_provenance"]["status"], "cannot_determine")
        self.assertEqual(result["findings"][0]["code"], "RW-P-W-001")

    def test_file_audit_reports_observable_marker_without_claiming_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.bin"
            original = b"header C2PA JUMBF payload"
            path.write_bytes(original)
            result = reviewwrite_provenance.audit_file(path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(result["source_provenance"]["status"], "signal_detected")
            self.assertEqual(
                {signal["name"] for signal in result["observable_signals"]},
                {"c2pa-content-credentials", "jumbf-content-credentials-container"},
            )
            self.assertIn("不等于完成来源归属认证", result["observable_signals"][0]["note"])

    def test_plain_text_reference_is_not_reported_as_embedded_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.md"
            path.write_text("本文讨论 C2PA、JUMBF 和 SynthID。", encoding="utf-8")
            result = reviewwrite_provenance.audit_file(path)
            self.assertEqual(result["source_provenance"]["status"], "reference_found")
            self.assertTrue(
                all(signal["status"] == "reference_found" for signal in result["observable_signals"])
            )

    def test_no_marker_is_unknown_not_negative_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plain.txt"
            path.write_text("普通文本", encoding="utf-8")
            result = reviewwrite_provenance.audit_file(path)
            self.assertEqual(result["source_provenance"]["status"], "cannot_determine")
            self.assertEqual(result["findings"][0]["code"], "RW-P-I-001")

    def test_docx_xml_is_scanned_without_modifying_container(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", "<w:t>正文\u202e</w:t>")
            original = path.read_bytes()
            result = reviewwrite_provenance.audit_file(path)
            self.assertEqual(path.read_bytes(), original)
            self.assertIn(
                "RW-P-W-001",
                {finding["code"] for finding in result["findings"]},
            )

    def test_pptx_xml_and_docx_embedded_media_distinction(self):
        with tempfile.TemporaryDirectory() as directory:
            pptx_path = Path(directory) / "deck.pptx"
            with zipfile.ZipFile(pptx_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("ppt/slides/slide1.xml", "<a:t>演示\u200b讨论 C2PA 标准</a:t>")
            pptx_result = reviewwrite_provenance.audit_file(pptx_path)
            self.assertEqual(pptx_result["source_provenance"]["status"], "reference_found")
            self.assertIn(
                "RW-P-W-001",
                {finding["code"] for finding in pptx_result["findings"]},
            )

            docx_media = Path(directory) / "with_media.docx"
            with zipfile.ZipFile(docx_media, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", "<w:t>普通正文</w:t>")
                archive.writestr("word/media/image1.jpg", b"\xff\xd8\xff C2PA JUMBF container")
            media_result = reviewwrite_provenance.audit_file(docx_media)
            self.assertEqual(media_result["source_provenance"]["status"], "signal_detected")
            self.assertTrue(
                any(item["status"] == "detected" for item in media_result["observable_signals"])
            )

    def test_cli_json_output(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "reviewwrite_provenance.py"),
                "--text",
                "文本",
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["input_kind"], "text")
        self.assertFalse(payload["preservation"]["source_markers_removed"])


if __name__ == "__main__":
    unittest.main()
