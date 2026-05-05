import unittest

from project_audit import analyze_project


class ProjectAuditTests(unittest.TestCase):
    def test_analyze_project_flags_large_files_and_risky_patterns(self):
        files = {
            "small.py": "print('ok')\n",
            "large.py": "\n".join(["x = 1"] * 201),
            "danger.py": "import os\nos.system('shutdown /s')\n",
            "broad.py": "try:\n    run()\nexcept Exception:\n    pass\n",
        }

        report = analyze_project(files, large_file_threshold=200)

        self.assertTrue(any(item["id"] == "large_files" for item in report["findings"]))
        self.assertTrue(any(item["id"] == "unsafe_process_calls" for item in report["findings"]))
        self.assertTrue(any(item["id"] == "broad_exception_handlers" for item in report["findings"]))
        self.assertGreaterEqual(len(report["recommendations"]), 3)

    def test_read_project_files_includes_tests_but_excludes_generated_cache(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_app.py").write_text("os.system('fake')\n", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "app.py").write_text("cached\n", encoding="utf-8")

            from project_audit import read_project_files

            files = read_project_files(root)

        self.assertIn("app.py", files)
        self.assertIn("LICENSE", files)
        normalized_paths = {path.replace("\\", "/") for path in files}
        self.assertIn("tests/test_app.py", normalized_paths)
        self.assertNotIn("__pycache__/app.py", normalized_paths)

    def test_audit_does_not_count_test_patterns_as_production_risk(self):
        files = {
            "app.py": "print('ok')\n",
            "tests/test_app.py": "os.system('fake')\nexcept Exception:\n    pass\n",
        }

        report = analyze_project(files)

        self.assertFalse(any(item["id"] == "unsafe_process_calls" for item in report["findings"]))
        self.assertFalse(any(item["id"] == "broad_exception_handlers" for item in report["findings"]))

    def test_audit_does_not_count_central_process_wrapper_as_unsafe_call_site(self):
        files = {
            "process_runner.py": "import subprocess\nsubprocess.run(['x'], shell=False)\n",
            "project_audit.py": '"subprocess.run("\n',
        }

        report = analyze_project(files)

        self.assertFalse(any(item["id"] == "unsafe_process_calls" for item in report["findings"]))

    def test_low_test_surface_uses_test_case_count_not_only_file_count(self):
        files = {
            "a.py": "x = 1\n",
            "b.py": "x = 2\n",
            "c.py": "x = 3\n",
            "tests/test_behaviors.py": "\n".join(
                [
                    "def test_one(): pass",
                    "def test_two(): pass",
                    "def test_three(): pass",
                    "def test_four(): pass",
                ]
            ),
        }

        report = analyze_project(files)

        self.assertFalse(any(item["id"] == "low_test_surface" for item in report["findings"]))

    def test_audit_flags_missing_oss_readiness_files(self):
        files = {
            "README.md": "# Project\n",
            "app.py": "print('ok')\n",
            "tests/test_app.py": "def test_app(): pass\n",
        }

        report = analyze_project(files)

        oss_finding = next(item for item in report["findings"] if item["id"] == "oss_readiness")
        missing = {item["path"] for item in oss_finding["items"]}

        self.assertIn("LICENSE", missing)
        self.assertIn("CHANGELOG.md", missing)
        self.assertIn(".github/pull_request_template.md", missing)

    def test_audit_accepts_required_oss_readiness_files(self):
        files = {
            "README.md": "# Project\n",
            "LICENSE": "MIT License\n",
            "CHANGELOG.md": "# Changelog\n",
            "CONTRIBUTING.md": "# Contributing\n",
            "CODE_OF_CONDUCT.md": "# Code of Conduct\n",
            "SECURITY.md": "# Security\n",
            ".github/pull_request_template.md": "## Checklist\n",
            ".github/ISSUE_TEMPLATE/bug_report.md": "---\nname: Bug report\n---\n",
            ".github/ISSUE_TEMPLATE/feature_request.md": "---\nname: Feature request\n---\n",
            ".github/ISSUE_TEMPLATE/performance_report.md": "---\nname: Performance report\n---\n",
            ".github/ISSUE_TEMPLATE/plugin_review.md": "---\nname: Plugin review\n---\n",
            ".github/workflows/ci.yml": "name: CI\n",
            "app.py": "print('ok')\n",
            "tests/test_app.py": "def test_app(): pass\n",
        }

        report = analyze_project(files)

        self.assertFalse(any(item["id"] == "oss_readiness" for item in report["findings"]))


if __name__ == "__main__":
    unittest.main()
