from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from public_release import build_public_release_check


class ReleaseReadinessTest(TestCase):
    def test_public_release_check_combines_docs_hygiene_quality_and_signing(self):
        check = build_public_release_check(
            env={"JARVIS_RELEASE_SIGNING_KEY": "1234567890123456"},
            hygiene_items=[],
            required_files=["README.md", "LICENSE", "CHANGELOG.md"],
            existing_files={"README.md", "LICENSE", "CHANGELOG.md"},
            trusted_signers=["ci"],
        )

        self.assertTrue(check["ready"])
        self.assertEqual(check["sections"]["hygiene"]["status"], "ready")
        self.assertEqual(check["sections"]["signing"]["status"], "ready")
        self.assertIn("python -m pytest", check["commands"])
        self.assertIn("python -m unittest discover -s tests -v", check["commands"])
        self.assertIn("python repo_hygiene.py --include-secrets", check["commands"])

    def test_public_source_release_allows_missing_optional_signing(self):
        check = build_public_release_check(
            env={},
            hygiene_items=[],
            required_files=["README.md"],
            existing_files={"README.md"},
            trusted_signers=["ci"],
        )

        self.assertTrue(check["ready"])
        self.assertEqual(check["sections"]["signing"]["status"], "optional")

    def test_readiness_cleans_only_cache_artifacts_created_during_check(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_cache = root / "__pycache__"
            generated_pyc = generated_cache / "public_release.cpython-311.pyc"
            calls = {"count": 0}

            def fake_hygiene(check_root: Path):
                calls["count"] += 1
                if calls["count"] == 1:
                    generated_cache.mkdir()
                    generated_pyc.write_bytes(b"cache")
                    return {
                        "passed": False,
                        "items": ["__pycache__", "__pycache__/public_release.cpython-311.pyc"],
                        "stdout": "",
                        "stderr": "",
                        "returncode": 1,
                    }
                return {"passed": True, "items": [], "stdout": "", "stderr": "", "returncode": 0}

            with patch("public_release._run_hygiene_subprocess", side_effect=fake_hygiene):
                check = build_public_release_check(
                    root=root,
                    env={},
                    required_files=[],
                    existing_files=set(),
                    trusted_signers=["ci"],
                )

            self.assertTrue(check["ready"])
            self.assertFalse(generated_pyc.exists())
            self.assertFalse(generated_cache.exists())
            self.assertIn("Removed readiness-generated cache artifact", check["sections"]["warnings"]["items"][0])

    def test_pre_existing_cache_artifacts_remain_release_blockers(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "__pycache__"
            cache_file = cache_dir / "old.cpython-311.pyc"
            cache_dir.mkdir()
            cache_file.write_bytes(b"old")

            check = build_public_release_check(
                root=root,
                env={},
                hygiene_items=["__pycache__", "__pycache__/old.cpython-311.pyc"],
                required_files=[],
                existing_files=set(),
                trusted_signers=["ci"],
            )

            self.assertFalse(check["ready"])
            self.assertTrue(cache_file.exists())
            self.assertIn("__pycache__", check["sections"]["hygiene"]["items"])
