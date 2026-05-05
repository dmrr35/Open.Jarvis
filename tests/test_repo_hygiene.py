import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from open_jarvis.release.repo_hygiene import clean_hygiene_items, find_hygiene_items, find_secret_patterns, render_hygiene_report


class RepoHygieneTests(unittest.TestCase):
    def test_find_hygiene_items_reports_generated_outputs_without_secrets_by_default(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("GROQ_API_KEY=secret\n", encoding="utf-8")
            (root / ".ruff_cache").mkdir()
            (root / "logs").mkdir()
            (root / "logs" / "runtime_events.jsonl").write_text("{}\n", encoding="utf-8")

            items = find_hygiene_items(root, include_secrets=False)

        paths = {item.path for item in items}
        self.assertIn(".ruff_cache", paths)
        self.assertIn("logs/runtime_events.jsonl", paths)
        self.assertNotIn(".env", paths)

    def test_find_hygiene_items_can_include_secrets_for_release_checks(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("GROQ_API_KEY=secret\n", encoding="utf-8")

            items = find_hygiene_items(root, include_secrets=True)

        self.assertIn(".env", {item.path for item in items})
        self.assertTrue(next(item for item in items if item.path == ".env").secret)

    def test_clean_hygiene_items_removes_generated_files_but_keeps_secrets_by_default(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("GROQ_API_KEY=secret\n", encoding="utf-8")
            (root / "build").mkdir()
            (root / "build" / "tmp.txt").write_text("generated\n", encoding="utf-8")

            removed = clean_hygiene_items(root)

            self.assertIn("build", removed)
            self.assertFalse((root / "build").exists())
            self.assertTrue((root / ".env").exists())

    def test_render_hygiene_report_documents_secret_status(self):
        report = render_hygiene_report(find_hygiene_items("."))

        self.assertIn("# Repository Hygiene", report)
        self.assertIn("Secret", report)

    def test_secret_scan_ignores_env_example_placeholders_and_flags_real_values(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.example").write_text("GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE\n", encoding="utf-8")
            (root / "config.py").write_text("api_key=sk-live-real-value\n", encoding="utf-8")

            findings = find_secret_patterns(root)

        self.assertEqual(len(findings), 1)
        self.assertIn("config.py:1", findings[0].path)
        self.assertTrue(findings[0].secret)


if __name__ == "__main__":
    unittest.main()
