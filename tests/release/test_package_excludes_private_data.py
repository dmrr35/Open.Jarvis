import tempfile
from pathlib import Path
from unittest import TestCase

from open_jarvis.release.windows_portable import assemble_portable_package


class PackageExcludesPrivateDataTest(TestCase):
    def test_assembly_does_not_copy_private_repo_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            app_build = root / "built" / "Open.Jarvis"
            output = root / "portable"
            app_build.mkdir(parents=True)
            (app_build / "Open.Jarvis.exe").write_bytes(b"fake exe")
            (repo / "logs").mkdir(parents=True)
            (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (repo / ".env.example").write_text("GROQ_API_KEY=\n", encoding="utf-8")
            (repo / ".env").write_text("GROQ_API_KEY=gsk_" + ("a" * 32), encoding="utf-8")
            (repo / "memory.json").write_text("{}", encoding="utf-8")
            (repo / "logs" / "jarvis.log").write_text("private\n", encoding="utf-8")

            assemble_portable_package(repo_root=repo, built_app_dir=app_build, portable_dir=output)

            self.assertFalse((output / ".env").exists())
            self.assertFalse((output / "memory.json").exists())
            self.assertFalse((output / "logs").exists())
