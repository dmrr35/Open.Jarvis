import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

from open_jarvis.release.windows_portable import build_windows_portable_plan, run_windows_portable_build


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
