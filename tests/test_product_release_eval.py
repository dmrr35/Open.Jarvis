"""Domain-focused product tests split from the former monolithic product feature suite."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from open_jarvis.evaluation.eval_artifacts import build_eval_artifact, compare_eval_artifacts, write_eval_artifacts
from open_jarvis.evaluation.eval_measurements import run_measured_eval_suite
from open_jarvis.evaluation.eval_runner import run_eval_suite
from open_jarvis.evaluation.evaluation_suite import build_eval_suite, summarize_eval_results
from open_jarvis.integrations.model_installer import (
    build_model_install_plan,
    build_signed_model_catalog,
    verify_model_catalog,
    verify_model_checksum,
)
from open_jarvis.integrations.model_installer import main as model_installer_main
from open_jarvis.release.release_build import build_release_artifacts, build_windows_release_plan, compute_file_sha256
from open_jarvis.release.release_build import main as release_build_main
from open_jarvis.security.release_security import build_key_rotation_plan, build_release_manifest, validate_release_environment
from open_jarvis.ui.release_panel import build_release_panel


class ProductReleaseEvalTest(TestCase):
    def test_release_manifest_and_environment_gate_are_operational(self):
        manifest = build_release_manifest("1.2.3", {"path": "dist/JARVIS.exe", "sha256": "abc"}, signer="ci")
        env = {"JARVIS_RELEASE_SIGNING_KEY": "12345678901234567890"}
        readiness = validate_release_environment(env, trusted_signers=["ci"])
        rotation = build_key_rotation_plan(last_rotated="2026-04-01", today="2026-04-27", rotation_days=90)

        self.assertEqual(manifest["signer"], "ci")
        self.assertEqual(manifest["artifact"]["sha256"], "abc")
        self.assertTrue(readiness["ready"])
        self.assertEqual(rotation["status"], "current")

    def test_release_panel_reports_signing_readiness(self):
        panel = build_release_panel({"JARVIS_RELEASE_SIGNING_KEY": "1234567890123456"}, trusted_signers=["ci"])

        self.assertTrue(panel["ready"])
        self.assertEqual(panel["checks"][0]["status"], "ready")

    def test_release_panel_reports_missing_key(self):
        panel = build_release_panel({}, trusted_signers=["ci"])

        self.assertFalse(panel["ready"])
        self.assertEqual(panel["checks"][0]["status"], "missing")

    def test_windows_release_plan_uses_pyinstaller_and_signed_manifest(self):
        plan = build_windows_release_plan("1.2.3", "arayuz.py", signing_ready=True)

        self.assertEqual(plan["status"], "ready")
        self.assertIn("pyinstaller", plan["commands"][0][0])
        self.assertTrue(plan["manifest"]["artifact"]["path"].endswith("JARVIS.exe"))
        self.assertTrue(plan["signing_required"])

    def test_release_artifacts_compute_hash_sign_manifest_and_write_reports(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            artifact_path = tmp_path / "JARVIS.exe"
            artifact_path.write_bytes(b"jarvis release bytes")
            output_dir = tmp_path / "release"

            result = build_release_artifacts(
                version="1.2.3",
                artifact_path=artifact_path,
                output_dir=output_dir,
                signing_key="12345678901234567890",
                signer="ci",
            )
            expected_sha256 = compute_file_sha256(artifact_path)

            manifest_path = Path(result["manifest_path"])
            signature_path = Path(result["signature_path"])

        self.assertEqual(result["artifact"]["sha256"], expected_sha256)
        self.assertEqual(result["verification"]["valid"], True)
        self.assertTrue(manifest_path.name.endswith(".manifest.json"))
        self.assertTrue(signature_path.name.endswith(".sig"))
        self.assertIn("size_bytes", result["artifact"])

    def test_release_build_cli_writes_manifest_for_existing_artifact(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            artifact_path = tmp_path / "JARVIS.exe"
            artifact_path.write_bytes(b"cli release bytes")
            output_dir = tmp_path / "release"

            exit_code = release_build_main(
                [
                    "--version",
                    "2.0.0",
                    "--artifact",
                    str(artifact_path),
                    "--output-dir",
                    str(output_dir),
                    "--signing-key",
                    "12345678901234567890",
                ]
            )

            manifest_path = output_dir / "jarvis-2.0.0.manifest.json"
            signature_path = output_dir / "jarvis-2.0.0.sig"
            manifest_exists = manifest_path.exists()
            signature_exists = signature_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(manifest_exists)
        self.assertTrue(signature_exists)

    def test_model_install_plan_is_explicit_and_safe(self):
        catalog = build_signed_model_catalog(signing_key="12345678901234567890")
        plan = build_model_install_plan("vosk-small-en-us", target_dir="models", catalog=catalog)

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["model"]["type"], "stt")
        self.assertTrue(plan["steps"][0]["safe"])
        self.assertIn("manual_download_url", plan["model"])
        self.assertEqual(plan["catalog_verification"]["status"], "verified")
        self.assertIn("expected_sha256", plan["model"])

    def test_signed_model_catalog_verifies_and_rejects_tampering(self):
        catalog = build_signed_model_catalog(signing_key="12345678901234567890")
        verified = verify_model_catalog(catalog, signing_key="12345678901234567890")
        tampered = dict(catalog)
        tampered["models"] = [dict(catalog["models"][0], sha256="0" * 64), *catalog["models"][1:]]

        self.assertEqual(verified["status"], "verified")
        self.assertEqual(verified["trusted_signer"], "ci")
        self.assertGreaterEqual(len(verified["models"]), 3)
        self.assertEqual(verify_model_catalog(tampered, signing_key="12345678901234567890")["status"], "invalid")

    def test_model_installer_cli_writes_signed_catalog(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "model-catalog.json"
            exit_code = model_installer_main(
                [
                    "--write-catalog",
                    str(output),
                    "--signing-key",
                    "12345678901234567890",
                ]
            )
            content = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn('"signature"', content)
        self.assertIn('"expected_sha256"', content)

    def test_model_checksum_verification_detects_valid_and_invalid_archives(self):
        with TemporaryDirectory() as tmp:
            model_file = Path(tmp) / "model.zip"
            model_file.write_text("offline model bytes", encoding="utf-8")

            valid = verify_model_checksum(model_file, "a74639497a8a390df903e58a2a513e0fea5db9ceb86e3f76ea2a2e9f49cfc2af")
            invalid = verify_model_checksum(model_file, "0" * 64)

        self.assertEqual(valid["status"], "verified")
        self.assertEqual(invalid["status"], "mismatch")

    def test_eval_suite_summarizes_intent_safety_latency_and_stt(self):
        suite = build_eval_suite()
        summary = summarize_eval_results(
            [
                {"id": "intent_open_app", "passed": True, "latency_ms": 40},
                {"id": "safety_shutdown_safe", "passed": True, "latency_ms": 10},
                {"id": "stt_wake_word", "passed": True, "latency_ms": 20},
            ]
        )

        self.assertGreaterEqual(len(suite["scenarios"]), 4)
        self.assertEqual(summary["status"], "pass")
        self.assertLessEqual(summary["average_latency_ms"], 50)

    def test_eval_runner_executes_builtin_deterministic_scenarios(self):
        result = run_eval_suite()

        self.assertEqual(result["summary"]["status"], "pass")
        self.assertGreaterEqual(result["summary"]["passed"], 4)
        self.assertTrue(all(item["passed"] for item in result["results"]))

    def test_measured_eval_suite_uses_router_stt_fixtures_and_real_latency(self):
        def router(prompt: str) -> dict[str, object]:
            routes: dict[str, dict[str, object]] = {
                "Open Chrome": {"action": "open_app", "params": {"app": "chrome"}},
                "Play music": {"action": "spotify_play", "params": {}},
                "Shut down the computer": {"action": "shutdown", "blocked": True},
                "What time is it?": {"action": "get_time", "params": {}},
            }
            return routes[prompt]

        result = run_measured_eval_suite(router=router, stt_fixtures={"stt_wake_word": "Jarvis"})

        self.assertEqual(result["summary"]["status"], "pass")
        self.assertEqual(result["measurement_mode"], "measured")
        self.assertTrue(all(item["latency_ms"] >= 0 for item in result["results"]))
        self.assertTrue(any(item["measurement_source"] == "command_router" for item in result["results"]))
        self.assertTrue(any(item["measurement_source"] == "stt_fixture" for item in result["results"]))

    def test_eval_runner_cli_can_write_measured_artifacts(self):
        from open_jarvis.evaluation.eval_runner import main as eval_runner_main

        with TemporaryDirectory() as tmp:
            exit_code = eval_runner_main(
                [
                    "--measured",
                    "--write-artifacts",
                    "--release-version",
                    "measured-test",
                    "--output-dir",
                    tmp,
                ]
            )
            artifact_path = Path(tmp) / "eval-artifact-measured-test.json"
            content = artifact_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn('"measurement_mode": "measured"', content)

    def test_eval_artifacts_write_json_and_markdown_release_reports(self):
        with TemporaryDirectory() as tmp:
            eval_result = run_eval_suite()
            artifact = build_eval_artifact(eval_result, release_version="1.2.3")
            written = write_eval_artifacts(artifact, output_dir=Path(tmp))

            json_report = Path(written["json"])
            markdown_report = Path(written["markdown"])
            markdown_content = markdown_report.read_text(encoding="utf-8")

        self.assertEqual(artifact["release_version"], "1.2.3")
        self.assertEqual(artifact["measurement_mode"], "deterministic")
        self.assertTrue(json_report.name.endswith(".json"))
        self.assertTrue(markdown_report.name.endswith(".md"))
        self.assertIn("Eval Artifact Report", markdown_content)

    def test_eval_artifact_comparison_reports_latency_and_pass_regressions(self):
        previous = {
            "summary": {"status": "pass", "passed": 5, "total": 5, "average_latency_ms": 20},
            "results": [{"id": "intent_open_app", "passed": True, "latency_ms": 20}],
        }
        current = {
            "summary": {"status": "fail", "passed": 4, "total": 5, "average_latency_ms": 45},
            "results": [{"id": "intent_open_app", "passed": False, "latency_ms": 80}],
        }

        comparison = compare_eval_artifacts(previous, current, latency_regression_ms=10)

        self.assertEqual(comparison["status"], "regressed")
        self.assertEqual(comparison["passed_delta"], -1)
        self.assertTrue(comparison["regressions"])
