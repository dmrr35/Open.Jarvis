import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

from open_jarvis.release.artifact_verifier import verify_release_artifact
from open_jarvis.release.windows_portable import assemble_portable_package, build_windows_portable_plan, run_windows_portable_build


class BuildScriptDryRunTest(TestCase):
    def test_build_plan_defaults_to_onedir_gui_entrypoint(self):
        plan = build_windows_portable_plan("v0.5.0")

        self.assertEqual(plan["artifact_name"], "Open.Jarvis-v0.5.0-windows-portable")
        self.assertIn("--onedir", plan["pyinstaller_command"])
        self.assertIn("arayuz.py", plan["pyinstaller_command"])

    def test_dry_run_does_not_create_final_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "release"
            result = run_windows_portable_build(version="v0.5.0", output_dir=output_dir, dry_run=True)

            self.assertEqual(result["status"], "dry_run")
            self.assertFalse((output_dir / "Open.Jarvis-v0.5.0-windows-portable.zip").exists())
            self.assertFalse((output_dir / "Open.Jarvis-v0.5.0-windows-portable").exists())

    def test_assemble_replaces_existing_output_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            built = root / "dist" / "Open.Jarvis"
            output = root / "release" / "Open.Jarvis-v0.5.0-windows-portable"
            built.mkdir(parents=True)
            output_config = output / "config"
            output_config.mkdir(parents=True)
            output_config.chmod(0o555)
            (built / "Open.Jarvis.exe").write_bytes(b"fake exe")
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / ".env.example").write_text("GROQ_API_KEY=\n", encoding="utf-8")

            result = assemble_portable_package(repo_root=root, built_app_dir=built, portable_dir=output)

            self.assertEqual(result["status"], "assembled")
            self.assertTrue((output / "config" / "README.txt").exists())

    def test_real_build_assembly_creates_verifiable_zip_when_pyinstaller_is_skipped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            built = root / "dist" / "Open.Jarvis"
            built.mkdir(parents=True)
            (built / "Open.Jarvis.exe").write_bytes(b"fake exe")
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / ".env.example").write_text("GROQ_API_KEY=\n", encoding="utf-8")
            current = Path.cwd()
            try:
                os.chdir(root)
                result = run_windows_portable_build(version="v0.5.0", skip_pyinstaller=True, clean=True)
            finally:
                os.chdir(current)

            zip_path = root / "release" / "Open.Jarvis-v0.5.0-windows-portable.zip"
            self.assertEqual(result["status"], "assembled")
            self.assertTrue(zip_path.exists())
            self.assertTrue(verify_release_artifact(zip_path)["passed"])

    def test_clean_removes_previous_pyinstaller_outputs_before_build(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stale_internal = root / "dist" / "Open.Jarvis" / "_internal" / "stale"
            stale_internal.mkdir(parents=True)
            stale_internal.chmod(0o555)
            (root / "build" / "Open.Jarvis").mkdir(parents=True)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / ".env.example").write_text("GROQ_API_KEY=\n", encoding="utf-8")

            def fake_pyinstaller(_command):
                built = root / "dist" / "Open.Jarvis"
                built.mkdir(parents=True)
                (built / "Open.Jarvis.exe").write_bytes(b"fake exe")
                return 0

            current = Path.cwd()
            try:
                os.chdir(root)
                result = run_windows_portable_build(version="v0.5.0", clean=True, runner=fake_pyinstaller)
            finally:
                os.chdir(current)

            self.assertEqual(result["status"], "assembled")
            self.assertFalse(stale_internal.exists())

    def test_cli_help_and_dry_run_succeed(self):
        help_result = subprocess.run([sys.executable, "scripts/build_windows_portable.py", "--help"], capture_output=True, text=True, check=False)
        dry_run = subprocess.run(
            [sys.executable, "scripts/build_windows_portable.py", "--version", "v0.5.0", "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(help_result.returncode, 0)
        self.assertEqual(dry_run.returncode, 0)
        self.assertIn("Open.Jarvis-v0.5.0-windows-portable", dry_run.stdout)
