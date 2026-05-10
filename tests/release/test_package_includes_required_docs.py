import tempfile
from pathlib import Path
from unittest import TestCase

from open_jarvis.release.artifact_verifier import verify_release_artifact
from open_jarvis.release.windows_portable import assemble_portable_package


class PackageIncludesRequiredDocsTest(TestCase):
    def test_assembly_includes_required_docs_and_guidance_folders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            app_build = root / "built" / "Open.Jarvis"
            output = root / "portable"
            app_build.mkdir(parents=True)
            (app_build / "Open.Jarvis.exe").write_bytes(b"fake exe")
            (repo / "docs").mkdir(parents=True)
            (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (repo / ".env.example").write_text("GROQ_API_KEY=\n", encoding="utf-8")
            (repo / "docs" / "WINDOWS_PORTABLE.md").write_text("Portable docs\n", encoding="utf-8")

            result = assemble_portable_package(repo_root=repo, built_app_dir=app_build, portable_dir=output)

            self.assertEqual(result["status"], "assembled")
            self.assertTrue((output / "README_FIRST.txt").exists())
            self.assertTrue((output / "LICENSE").exists())
            self.assertTrue((output / ".env.example").exists())
            self.assertTrue((output / "docs" / "WINDOWS_PORTABLE.md").exists())
            self.assertTrue((output / "plugins" / "README.txt").exists())
            self.assertTrue(verify_release_artifact(output)["passed"])
