from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from command_history import CommandHistory
from command_suggestions import suggest_commands
from e2e_readiness import build_e2e_readiness_plan
from error_messages import build_user_error
from eval_artifacts import build_eval_artifact, compare_eval_artifacts, write_eval_artifacts
from eval_measurements import run_measured_eval_suite
from eval_runner import run_eval_suite
from evaluation_suite import build_eval_suite, summarize_eval_results
from feature_quality import build_feature_catalog, build_feature_quality_report, render_feature_quality_report
from llm_fallback import build_provider_result, resolve_ai_mode, select_llm_provider
from maintenance import build_maintenance_plan
from memory_panel import build_memory_panel, delete_note, update_preference
from model_installer import build_model_install_plan, build_signed_model_catalog, verify_model_catalog, verify_model_checksum
from model_installer import main as model_installer_main
from offline_profile import build_offline_profile
from onboarding_engine import build_onboarding_result
from performance_benchmarks import build_performance_budget, summarize_benchmark_results
from permission_profiles import action_allowed, build_permission_matrix, get_active_permission_profile
from privacy_mode import build_privacy_session, mask_sensitive_text, mask_sensitive_value
from release_build import build_release_artifacts, build_windows_release_plan, compute_file_sha256
from release_build import main as release_build_main
from release_panel import build_release_panel
from release_security import build_key_rotation_plan, build_release_manifest, validate_release_environment
from security_center import build_security_overview
from tts_provider import build_tts_provider_options, select_tts_provider
from user_profiles import build_user_profile, merge_user_profile
from voice_calibration import build_calibration_recommendation
from workflow_engine import build_workflow_plan


class ProductFeaturesTest(TestCase):
    def test_onboarding_result_returns_statuses_and_fix_commands(self):
        result = build_onboarding_result({"GROQ_API_KEY": "g", "JARVIS_ENERGY_THRESHOLD": "450"})

        by_id = {step["id"]: step for step in result["steps"]}
        self.assertEqual(by_id["groq"]["status"], "ready")
        self.assertEqual(by_id["spotify"]["status"], "needs_setup")
        self.assertTrue(by_id["spotify"]["fix_command"].startswith("setx SPOTIFY_CLIENT_ID"))
        self.assertGreaterEqual(result["summary"]["ready"], 2)

    def test_onboarding_result_handles_empty_environment(self):
        result = build_onboarding_result({})

        self.assertGreaterEqual(result["summary"]["needs_setup"], 3)
        self.assertEqual(result["summary"]["optional"], 1)

    def test_permission_profiles_block_or_allow_risky_actions(self):
        self.assertFalse(action_allowed("shutdown", "safe"))
        self.assertTrue(action_allowed("open_web", "safe"))
        self.assertTrue(action_allowed("shutdown", "admin"))
        self.assertEqual(get_active_permission_profile({"JARVIS_PERMISSION_PROFILE": "admin"})["id"], "admin")
        self.assertEqual(get_active_permission_profile({"JARVIS_PERMISSION_PROFILE": "unknown"})["id"], "normal")

        matrix = build_permission_matrix(["open_web", "shutdown"])
        self.assertEqual(matrix["shutdown"]["safe"], "blocked")
        self.assertEqual(matrix["shutdown"]["admin"], "allowed")

    def test_security_overview_summarizes_permission_privacy_and_secret_status(self):
        overview = build_security_overview(
            {
                "JARVIS_PERMISSION_PROFILE": "safe",
                "JARVIS_PRIVACY_MODE": "true",
                "GROQ_API_KEY": "secret",
                "SPOTIFY_CLIENT_SECRET": "",
            },
            actions=["open_web", "shutdown"],
        )

        self.assertEqual(overview["profile"]["id"], "safe")
        self.assertTrue(overview["privacy"]["enabled"])
        self.assertEqual(overview["secrets"]["GROQ_API_KEY"], "CONFIGURED")
        self.assertEqual(overview["secrets"]["SPOTIFY_CLIENT_SECRET"], "MISSING")
        self.assertEqual(overview["permission_matrix"]["shutdown"]["safe"], "blocked")
        self.assertIn("shutdown", overview["confirmation_required"])

    def test_memory_panel_can_update_and_delete_user_visible_memory(self):
        memory = {"preferences": {"wake_word": "jarvis"}, "notes": ["a", "b"], "habits": {"music": 3}}

        updated = update_preference(memory, "favorite_app", "Chrome")
        trimmed = delete_note(updated, 0)
        panel = build_memory_panel(trimmed)

        self.assertEqual(panel["preferences"]["favorite_app"], "Chrome")
        self.assertEqual(panel["notes"], ["b"])
        self.assertEqual(panel["counts"]["habits"], 1)

    def test_memory_panel_exposes_privacy_controls_without_leaking_raw_secrets(self):
        memory = {
            "preferences": {"GROQ_API_KEY": "secret", "favorite_app": "Chrome"},
            "notes": [{"text": "first"}, {"text": "second"}],
            "habits": {"music": 3},
        }

        panel = build_memory_panel(memory, privacy_enabled=True)

        self.assertEqual(panel["privacy"]["memory_writes"], "disabled")
        self.assertEqual(panel["preferences"]["GROQ_API_KEY"], "***")
        self.assertEqual(panel["recent_notes"], [{"text": "first"}, {"text": "second"}])

    def test_command_history_records_undoable_actions(self):
        calls = []
        history = CommandHistory(limit=2)

        first = history.record("set volume", undo=lambda: calls.append("undo-volume"))
        history.record("open browser")
        history.record("play music")

        self.assertEqual([item["command"] for item in history.list()], ["open browser", "play music"])
        self.assertEqual(history.undo(first["id"])["status"], "expired")
        self.assertEqual(history.undo(history.list()[-1]["id"])["status"], "not_undoable")
        undoable = history.record("set volume", undo=lambda: calls.append("undo-volume"))
        self.assertEqual(history.undo(undoable["id"])["status"], "undone")
        self.assertEqual(calls, ["undo-volume"])

    def test_llm_fallback_prefers_cloud_then_local_then_rules(self):
        self.assertEqual(select_llm_provider({"GROQ_API_KEY": "g"})["provider"], "groq")
        self.assertEqual(select_llm_provider({"JARVIS_LOCAL_LLM_URL": "http://127.0.0.1:11434"})["provider"], "local")
        self.assertEqual(select_llm_provider({})["provider"], "rules")

    def test_ai_mode_respects_explicit_rules_and_auto_selection(self):
        explicit = resolve_ai_mode({"JARVIS_AI_MODE": "rules", "GROQ_API_KEY": "g"})
        automatic = resolve_ai_mode({"JARVIS_AI_MODE": "auto", "GROQ_API_KEY": "g"})

        self.assertEqual(explicit["provider"], "rules")
        self.assertEqual(explicit["mode"], "rules")
        self.assertEqual(automatic["provider"], "groq")

    def test_provider_result_has_stable_shape_for_future_providers(self):
        result = build_provider_result(
            ok=False,
            provider="groq",
            mode="free_cloud",
            action={"action": "talk", "params": {}},
            error="rate_limited",
            latency_ms=42.5,
        )

        self.assertEqual(result["provider"], "groq")
        self.assertEqual(result["mode"], "free_cloud")
        self.assertFalse(result["ok"])
        self.assertEqual(result["latency_ms"], 42.5)

    def test_workflow_plan_turns_steps_into_safe_executable_plan(self):
        plan = build_workflow_plan("research", ["search topic", "summarize", "save notes"])

        self.assertEqual(plan["status"], "ready")
        self.assertEqual([step["order"] for step in plan["steps"]], [1, 2, 3])
        self.assertTrue(all(step["rollback"] for step in plan["steps"]))

    def test_workflow_plan_handles_empty_steps(self):
        plan = build_workflow_plan("empty", ["", "   "])

        self.assertEqual(plan["status"], "empty")
        self.assertEqual(plan["steps"], [])

    def test_maintenance_plan_recommends_safe_cleanup_actions(self):
        plan = build_maintenance_plan({"log_bytes": 2_000_000, "memory_score": 40, "cache_bytes": 3_000_000})

        self.assertEqual([item["id"] for item in plan["actions"]], ["prune_memory", "rotate_logs", "trim_cache"])
        self.assertTrue(all(item["safe"] for item in plan["actions"]))

    def test_maintenance_plan_stays_empty_when_metrics_are_healthy(self):
        plan = build_maintenance_plan({"log_bytes": 10, "memory_score": 90, "cache_bytes": 10})

        self.assertEqual(plan["actions"], [])

    def test_user_profile_merge_keeps_isolated_preferences(self):
        base = build_user_profile("ali")
        merged = merge_user_profile(base, {"wake_word": "friday", "permission_profile": "safe"})

        self.assertEqual(merged["id"], "ali")
        self.assertEqual(merged["settings"]["wake_word"], "friday")
        self.assertEqual(merged["settings"]["permission_profile"], "safe")

    def test_suggestions_follow_context_and_security_mode(self):
        suggestions = suggest_commands({"last_action": "music", "permission_profile": "safe", "missing": ["spotify"]})

        self.assertEqual(suggestions[0]["command"], "finish spotify setup")
        self.assertTrue(any(item["category"] == "music" for item in suggestions))
        self.assertTrue(all("shutdown" not in item["command"] for item in suggestions))

    def test_suggestions_include_runtime_option_outside_safe_mode(self):
        suggestions = suggest_commands({"permission_profile": "normal"})

        self.assertTrue(any(item["category"] == "runtime" for item in suggestions))

    def test_release_panel_reports_signing_readiness(self):
        panel = build_release_panel({"JARVIS_RELEASE_SIGNING_KEY": "1234567890123456"}, trusted_signers=["ci"])

        self.assertTrue(panel["ready"])
        self.assertEqual(panel["checks"][0]["status"], "ready")

    def test_release_panel_reports_missing_key(self):
        panel = build_release_panel({}, trusted_signers=["ci"])

        self.assertFalse(panel["ready"])
        self.assertEqual(panel["checks"][0]["status"], "missing")

    def test_privacy_mode_masks_sensitive_values_and_marks_ephemeral(self):
        self.assertEqual(mask_sensitive_text("GROQ_API_KEY=abc123 and token=secret"), "GROQ_API_KEY=*** and token=***")
        self.assertEqual(mask_sensitive_value({"token": "secret", "note": "PASSWORD=abc"}), {"token": "***", "note": "PASSWORD=***"})

        session = build_privacy_session(enabled=True)
        self.assertEqual(session["memory_writes"], "disabled")
        self.assertEqual(session["retention"], "ephemeral")

    def test_privacy_mode_off_keeps_normal_retention(self):
        session = build_privacy_session(enabled=False)

        self.assertEqual(session["memory_writes"], "enabled")
        self.assertEqual(session["retention"], "normal")

    def test_error_messages_use_reason_and_action_format(self):
        message = build_user_error("Spotify failed", reason="Credentials are missing", fix="Finish Spotify setup")

        self.assertIn("Reason: Credentials are missing", message)
        self.assertIn("Next step: Finish Spotify setup", message)

    def test_e2e_readiness_plan_covers_critical_desktop_flows(self):
        plan = build_e2e_readiness_plan(["ui_start", "voice_command", "onboarding", "permission_profile"])

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["coverage_target"], "desktop-critical")
        self.assertEqual(len(plan["flows"]), 4)

    def test_feature_quality_report_tracks_all_core_features(self):
        catalog = build_feature_catalog()
        report = build_feature_quality_report()

        self.assertGreaterEqual(len(catalog), 10)
        self.assertEqual(report["weak"], [])
        self.assertEqual(report["production_ready"], report["total"])
        self.assertGreaterEqual(report["average_score"], 90)
        self.assertTrue(all(feature["tests"] for feature in catalog))
        self.assertTrue(all(feature["performance_budget_ms"] > 0 for feature in catalog))
        self.assertTrue(all(feature["next_improvement"] for feature in catalog))

    def test_feature_quality_report_renders_cli_table(self):
        rendered = render_feature_quality_report()

        self.assertIn("Feature Quality Report", rendered)
        self.assertIn("Average score", rendered)
        self.assertIn("onboarding", rendered)

    def test_tts_provider_selector_exposes_medium_roadmap_choice(self):
        options = build_tts_provider_options()
        selected = select_tts_provider({"JARVIS_TTS_PROVIDER": "edge"})

        self.assertIn("edge", [item["id"] for item in options])
        self.assertEqual(selected["id"], "edge")
        self.assertTrue(selected["available"])

    def test_release_manifest_and_environment_gate_are_operational(self):
        manifest = build_release_manifest("1.2.3", {"path": "dist/JARVIS.exe", "sha256": "abc"}, signer="ci")
        env = {"JARVIS_RELEASE_SIGNING_KEY": "12345678901234567890"}
        readiness = validate_release_environment(env, trusted_signers=["ci"])
        rotation = build_key_rotation_plan(last_rotated="2026-04-01", today="2026-04-27", rotation_days=90)

        self.assertEqual(manifest["signer"], "ci")
        self.assertEqual(manifest["artifact"]["sha256"], "abc")
        self.assertTrue(readiness["ready"])
        self.assertEqual(rotation["status"], "current")

    def test_offline_profile_covers_local_stt_tts_and_llm(self):
        profile = build_offline_profile(
            {"JARVIS_OFFLINE_STT": "1", "JARVIS_TTS_PROVIDER": "piper", "JARVIS_LOCAL_LLM_URL": "http://127.0.0.1:11434"}
        )

        self.assertEqual(profile["status"], "ready")
        self.assertEqual([item["id"] for item in profile["components"]], ["stt", "tts", "llm"])
        self.assertTrue(all(item["local"] for item in profile["components"]))

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
        from eval_runner import main as eval_runner_main

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

    def test_voice_calibration_recommends_threshold_from_noise_samples(self):
        recommendation = build_calibration_recommendation([120, 140, 160, 180], safety_margin=80)

        self.assertEqual(recommendation["status"], "ready")
        self.assertEqual(recommendation["recommended_threshold"], 230)
        self.assertIn("JARVIS_ENERGY_THRESHOLD=230", recommendation["env_line"])

    def test_performance_budget_marks_slow_results_as_failures(self):
        budget = build_performance_budget()
        summary = summarize_benchmark_results(
            [
                {"id": "startup", "duration_ms": 900},
                {"id": "command_route", "duration_ms": 1200},
            ],
            budget,
        )

        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["failed"], 1)
