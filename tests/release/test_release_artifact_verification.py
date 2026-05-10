import tempfile
import zipfile
from pathlib import Path
from unittest import TestCase

from open_jarvis.release.artifact_verifier import verify_release_artifact


def _write_valid_package(root: Path) -> Path:
    portable = root / "portable"
    app = portable / "Open.Jarvis"
    app.mkdir(parents=True)
    (app / "Open.Jarvis.exe").write_bytes(b"fake exe")
    (portable / "README_FIRST.txt").write_text("Read this first.\n", encoding="utf-8")
    (portable / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (portable / ".env.example").write_text("GROQ_API_KEY=\n", encoding="utf-8")
    return portable


class ReleaseArtifactVerificationTest(TestCase):
    def test_valid_folder_artifact_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            portable = _write_valid_package(Path(temp_dir))

            result = verify_release_artifact(portable)

            self.assertTrue(result["passed"])

    def test_valid_zip_artifact_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            portable = _write_valid_package(root)
            archive = root / "portable.zip"
            with zipfile.ZipFile(archive, "w") as package:
                for file_path in portable.rglob("*"):
                    if file_path.is_file():
                        package.write(file_path, file_path.relative_to(portable).as_posix())

            result = verify_release_artifact(archive)

            self.assertTrue(result["passed"])

    def test_rejects_env_private_logs_and_unexpected_exe(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            portable = _write_valid_package(Path(temp_dir))
            (portable / ".env").write_text("GROQ_API_KEY=gsk_" + ("a" * 32), encoding="utf-8")
            (portable / "logs").mkdir()
            (portable / "logs" / "jarvis.log").write_text("private", encoding="utf-8")
            (portable / "helper.exe").write_bytes(b"unexpected")

            result = verify_release_artifact(portable)

            reasons = " ".join(finding["reason"] for finding in result["findings"])
            self.assertFalse(result["passed"])
            self.assertIn(".env", reasons)
            self.assertIn("log", reasons)
            self.assertIn("unexpected executable", reasons)

    def test_rejects_local_path_leakage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            portable = _write_valid_package(Path(temp_dir))
            (portable / "README_FIRST.txt").write_text(r"Use C:\Users\Alice\secret.txt", encoding="utf-8")

            result = verify_release_artifact(portable)

            self.assertFalse(result["passed"])
            self.assertTrue(any("local path" in finding["reason"] for finding in result["findings"]))

    def test_rejects_zip_traversal_and_nested_zip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir) / "bad.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../escape.txt", "bad")
                package.writestr("Open.Jarvis/Open.Jarvis.exe", "fake")
                package.writestr("README_FIRST.txt", "read")
                package.writestr("LICENSE", "MIT")
                package.writestr(".env.example", "GROQ_API_KEY=")
                package.writestr("nested.zip", "bad")

            result = verify_release_artifact(archive)

            self.assertFalse(result["passed"])
            self.assertTrue(any("traversal" in finding["reason"] for finding in result["findings"]))
            self.assertTrue(any("nested archive" in finding["reason"] for finding in result["findings"]))

    def test_verifier_cli_help_succeeds(self):
        import subprocess
        import sys

        result = subprocess.run([sys.executable, "scripts/verify_release_artifact.py", "--help"], capture_output=True, text=True, check=False)

        self.assertEqual(result.returncode, 0)
