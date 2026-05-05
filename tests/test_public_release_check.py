import tempfile
import unittest
from pathlib import Path

from scripts.public_release_check import run_check


class PublicReleaseCheckTests(unittest.TestCase):
    def test_safe_placeholders_pass(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.example").write_text(
                "\n".join(
                    [
                        "GROQ_API_KEY=",
                        "SPOTIFY_CLIENT_ID=",
                        "SPOTIFY_CLIENT_SECRET=",
                        "SPOTIFY_REDIRECT_URI=",
                        "JARVIS_ENABLE_GROQ=false",
                        "JARVIS_ENABLE_SPOTIFY=false",
                        "CONTACT_EMAIL=example@example.com",
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(run_check(root), [])

    def test_real_secret_patterns_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.txt").write_text("GROQ_API_KEY=gsk_" + ("a" * 32), encoding="utf-8")

            findings = run_check(root)

            self.assertTrue(findings)
            self.assertTrue(any("Groq API key pattern" in finding.reason for finding in findings))

    def test_private_runtime_artifacts_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "memory.json").write_text("{}", encoding="utf-8")

            findings = run_check(root)

            self.assertTrue(findings)
            self.assertTrue(any("private runtime/credential filename" in finding.reason for finding in findings))

    def test_machine_specific_user_path_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text(r"Use C:\Users\Alice\secret.txt", encoding="utf-8")

            findings = run_check(root)

            self.assertTrue(findings)
            self.assertTrue(any("machine-specific Windows user path" in finding.reason for finding in findings))


if __name__ == "__main__":
    unittest.main()
