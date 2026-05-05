import unittest
from unittest.mock import patch

import kontrol
from jarvis_admin import render_health_report


class HealthCliTests(unittest.TestCase):
    def test_should_pause_skips_ci_and_no_pause_flag(self):
        self.assertFalse(kontrol.should_pause(["kontrol.py", "--no-pause"], {}))
        self.assertFalse(kontrol.should_pause(["kontrol.py"], {"CI": "true"}))
        self.assertTrue(kontrol.should_pause(["kontrol.py"], {}))

    def test_project_audit_check_reports_findings(self):
        with patch("kontrol.read_project_files", return_value={"large.py": "\n".join(["x = 1"] * 501)}):
            result = kontrol._check_project_audit()

        self.assertEqual(result["id"], "project_audit")
        self.assertEqual(result["severity"], "warning")
        self.assertIn("finding", result["detail"])

    def test_main_does_not_prompt_when_no_pause_flag_is_used(self):
        with (
            patch(
                "kontrol._check_python_version", return_value={"id": "python", "severity": "ok", "title": "Python", "detail": "", "fix": ""}
            ),
            patch("kontrol._check_chrome", return_value={"id": "chrome", "severity": "ok", "title": "Chrome", "detail": "", "fix": ""}),
            patch(
                "kontrol._check_internet", return_value={"id": "internet", "severity": "ok", "title": "Internet", "detail": "", "fix": ""}
            ),
            patch(
                "kontrol._check_memory_health", return_value={"id": "memory", "severity": "ok", "title": "Memory", "detail": "", "fix": ""}
            ),
            patch(
                "kontrol._check_runtime_posture",
                return_value={"id": "runtime", "severity": "ok", "title": "Runtime", "detail": "", "fix": ""},
            ),
            patch(
                "kontrol._check_release_signing",
                return_value={"id": "release", "severity": "ok", "title": "Release", "detail": "", "fix": ""},
            ),
            patch(
                "kontrol._check_project_audit", return_value={"id": "audit", "severity": "ok", "title": "Audit", "detail": "", "fix": ""}
            ),
            patch("kontrol.build_health_checks", return_value=[]),
            patch("kontrol.build_provider_health_checks", return_value=[]),
            patch("builtins.input") as input_mock,
        ):
            result = kontrol.main(["kontrol.py", "--no-pause"])

        self.assertEqual(result, 0)
        input_mock.assert_not_called()

    def test_main_enables_explicit_provider_probe_flag(self):
        with (
            patch("kontrol._check_python_version", return_value={"id": "python", "severity": "ok", "title": "Python", "detail": "", "fix": ""}),
            patch("kontrol._check_chrome", return_value={"id": "chrome", "severity": "ok", "title": "Chrome", "detail": "", "fix": ""}),
            patch("kontrol._check_internet", return_value={"id": "internet", "severity": "ok", "title": "Internet", "detail": "", "fix": ""}),
            patch("kontrol._check_memory_health", return_value={"id": "memory", "severity": "ok", "title": "Memory", "detail": "", "fix": ""}),
            patch("kontrol._check_runtime_posture", return_value={"id": "runtime", "severity": "ok", "title": "Runtime", "detail": "", "fix": ""}),
            patch("kontrol._check_release_signing", return_value={"id": "release", "severity": "ok", "title": "Release", "detail": "", "fix": ""}),
            patch("kontrol._check_project_audit", return_value={"id": "audit", "severity": "ok", "title": "Audit", "detail": "", "fix": ""}),
            patch("kontrol.build_health_checks", return_value=[]),
            patch("kontrol.build_provider_health_checks", return_value=[]) as provider_checks,
        ):
            result = kontrol.main(["kontrol.py", "--probe-providers", "--no-pause"])

        self.assertEqual(result, 0)
        self.assertTrue(provider_checks.call_args.kwargs["probe_local"])

    def test_health_report_renders_fix_commands_when_available(self):
        report = render_health_report(
            [
                {
                    "id": "spotify",
                    "severity": "warning",
                    "title": "Spotify",
                    "detail": "Missing credentials.",
                    "fix": "Add Spotify credentials.",
                    "fix_command": "notepad .env",
                }
            ]
        )

        self.assertIn("Fix command: notepad .env", report)


if __name__ == "__main__":
    unittest.main()
