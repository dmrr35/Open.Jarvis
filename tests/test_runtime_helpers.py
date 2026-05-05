import unittest
from unittest.mock import patch

from memory import build_memory_health_report, get_memory_quality_score, prune_memory
from observability import build_runtime_event_snapshot, format_runtime_event, read_runtime_events
from plugin_security import (
    build_plugin_sandbox_policy,
    validate_plugin_manifest,
)
from process_runner import launch_process
from release_security import (
    build_release_smoke_check,
    sign_release_payload,
    verify_release_signature,
)


class RuntimeHelpersTest(unittest.TestCase):
    def test_launch_process_requires_argument_sequence(self):
        with self.assertRaises(TypeError):
            launch_process("notepad.exe")

    @patch("process_runner.subprocess.Popen")
    def test_launch_process_uses_shellless_sequence(self, popen_mock):
        launch_process(["notepad.exe"])

        popen_mock.assert_called_once_with(["notepad.exe"], shell=False)

    def test_prune_memory_keeps_recent_notes_and_caps_short_term(self):
        memory = {
            "preferences": {"favorite_music": None, "favorite_app": None, "preferred_volume": None, "wake_word": "jarvis", "custom": {}},
            "habits": {"open chrome": 4},
            "notes": [{"text": f"note {i}", "created_at": f"2026-04-14 10:{i:02d}"} for i in range(8)],
            "created_at": "2026-04-14T10:00:00",
            "last_seen": "2026-04-14T10:10:00",
            "total_commands": 20,
        }

        result = prune_memory(memory, max_notes=5)

        self.assertEqual(len(result["notes"]), 5)
        self.assertEqual(result["notes"][0]["text"], "note 3")

    def test_memory_quality_score_reacts_to_usage_and_notes(self):
        memory = {
            "preferences": {
                "favorite_music": "Eminem",
                "favorite_app": "chrome",
                "preferred_volume": 70,
                "wake_word": "jarvis",
                "custom": {},
            },
            "habits": {"open chrome": 10, "play eminem": 6},
            "notes": [{"text": "buy milk", "created_at": "2026-04-14 10:00"}],
            "created_at": "2026-04-14T10:00:00",
            "last_seen": "2026-04-14T10:10:00",
            "total_commands": 25,
        }

        score = get_memory_quality_score(memory)

        self.assertGreaterEqual(score, 70)

    def test_build_memory_health_report_mentions_pruning(self):
        memory = {
            "preferences": {"favorite_music": None, "favorite_app": None, "preferred_volume": None, "wake_word": "jarvis", "custom": {}},
            "habits": {},
            "notes": [],
            "created_at": "2026-04-14T10:00:00",
            "last_seen": "2026-04-14T10:10:00",
            "total_commands": 0,
        }

        report = build_memory_health_report(memory)

        self.assertIn("Pruning", report["recommendation"])
        self.assertLess(report["score"], 70)

    def test_validate_plugin_manifest_accepts_trusted_manifest(self):
        manifest = {
            "name": "sample_plugin",
            "version": "1.0.0",
            "entrypoint": "main.py",
            "signer": "ci",
            "actions": ["open_web"],
            "trusted": True,
        }

        result = validate_plugin_manifest(manifest, trusted_signers=["ci"])

        self.assertTrue(result["valid"])
        self.assertEqual(result["policy"]["execution"], "isolated")

    def test_validate_plugin_manifest_rejects_untrusted_signer(self):
        manifest = {
            "name": "sample_plugin",
            "version": "1.0.0",
            "entrypoint": "main.py",
            "signer": "unknown",
            "actions": ["open_web"],
        }

        result = validate_plugin_manifest(manifest, trusted_signers=["ci"])

        self.assertFalse(result["valid"])
        self.assertIn("signer", result["issues"][0])

    def test_validate_plugin_manifest_rejects_path_traversal_entrypoint(self):
        manifest = {
            "name": "sample_plugin",
            "version": "1.0.0",
            "entrypoint": "../outside.py",
            "signer": "ci",
            "actions": ["open_web"],
        }

        result = validate_plugin_manifest(manifest, trusted_signers=["ci"])

        self.assertFalse(result["valid"])
        self.assertTrue(any("entrypoint" in issue for issue in result["issues"]))

    def test_build_plugin_sandbox_policy_is_conservative(self):
        policy = build_plugin_sandbox_policy()

        self.assertEqual(policy["execution"], "isolated")
        self.assertIn("timeout_seconds", policy)

    def test_release_signature_round_trip_uses_trusted_signer(self):
        import os

        original = os.environ.get("JARVIS_RELEASE_SIGNING_KEY")
        os.environ["JARVIS_RELEASE_SIGNING_KEY"] = "x" * 16
        try:
            payload = {"version": "1.0.0", "artifact": {"name": "jarvis"}}
            signature = sign_release_payload(payload, signer="ci")
            result = verify_release_signature(payload, signature, signer="ci")
            self.assertTrue(result["valid"])
        finally:
            if original is None:
                os.environ.pop("JARVIS_RELEASE_SIGNING_KEY", None)
            else:
                os.environ["JARVIS_RELEASE_SIGNING_KEY"] = original

    def test_release_smoke_check_returns_policy(self):
        import os

        original = os.environ.get("JARVIS_RELEASE_SIGNING_KEY")
        os.environ["JARVIS_RELEASE_SIGNING_KEY"] = "x" * 16
        try:
            result = build_release_smoke_check("1.0.0", {"name": "jarvis"})
            self.assertTrue(result["verification"]["valid"])
            self.assertEqual(result["policy"]["trusted_signers"], ["ci"])
        finally:
            if original is None:
                os.environ.pop("JARVIS_RELEASE_SIGNING_KEY", None)
            else:
                os.environ["JARVIS_RELEASE_SIGNING_KEY"] = original

    def test_release_signature_rejects_untrusted_signer(self):
        import os

        original = os.environ.get("JARVIS_RELEASE_SIGNING_KEY")
        os.environ["JARVIS_RELEASE_SIGNING_KEY"] = "x" * 16
        try:
            payload = {"version": "1.0.0"}
            signature = sign_release_payload(payload, signer="ci")
            result = verify_release_signature(payload, signature, signer="external")
            self.assertFalse(result["valid"])
            self.assertIn("untrusted", result["reason"])
        finally:
            if original is None:
                os.environ.pop("JARVIS_RELEASE_SIGNING_KEY", None)
            else:
                os.environ["JARVIS_RELEASE_SIGNING_KEY"] = original

    def test_format_runtime_event_includes_context(self):
        event = {
            "timestamp": "2026-04-14T10:00:00",
            "severity": "warning",
            "event_type": "groq_error",
            "detail": "Groq analysis failed",
            "context": {"error": "timeout"},
        }

        rendered = format_runtime_event(event)

        self.assertIn("[WARNING]", rendered)
        self.assertIn("groq_error", rendered)
        self.assertIn("context: error=timeout", rendered)

    def test_read_runtime_events_ignores_malformed_json_lines(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            event_file = Path(temp_dir) / "runtime_events.jsonl"
            event_file.write_text(
                '{"timestamp": "2026-04-14T10:00:00", "severity": "info"}\nnot-json\n',
                encoding="utf-8",
            )
            with patch("observability.EVENT_LOG", event_file):
                events = read_runtime_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["severity"], "info")

    def test_read_runtime_events_returns_recent_valid_events_with_limit(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            event_file = Path(temp_dir) / "runtime_events.jsonl"
            event_file.write_text(
                "\n".join(
                    [
                        '{"timestamp": "2026-04-14T10:00:00", "severity": "info", "event_type": "old"}',
                        "not-json",
                        '{"timestamp": "2026-04-14T10:01:00", "severity": "warning", "event_type": "middle"}',
                        '{"timestamp": "2026-04-14T10:02:00", "severity": "error", "event_type": "new"}',
                    ]
                ),
                encoding="utf-8",
            )
            with patch("observability.EVENT_LOG", event_file):
                events = read_runtime_events(limit=2)

        self.assertEqual([event["event_type"] for event in events], ["middle", "new"])

    @patch("observability.read_runtime_events")
    @patch("observability.build_slo_report")
    def test_build_runtime_event_snapshot_orders_newest_first(self, build_slo_report_mock, read_runtime_events_mock):
        read_runtime_events_mock.return_value = [
            {"timestamp": "2026-04-14T10:00:00", "severity": "info", "event_type": "startup", "detail": "started", "context": {}},
            {"timestamp": "2026-04-14T10:01:00", "severity": "error", "event_type": "voice_error", "detail": "failed", "context": {}},
        ]
        build_slo_report_mock.return_value = {
            "status": "degraded",
            "events_seen": 2,
            "warning_count": 0,
            "error_count": 1,
            "recommendation": "Review recent runtime errors.",
        }

        snapshot = build_runtime_event_snapshot(limit=10)

        self.assertEqual(snapshot["report"]["status"], "degraded")
        self.assertTrue(snapshot["formatted_events"][0].startswith("[ERROR]"))
        self.assertTrue(snapshot["formatted_events"][1].startswith("[INFO]"))

    @patch("observability.read_runtime_events")
    @patch("observability.build_slo_report")
    def test_build_runtime_event_snapshot_filters_by_severity(self, build_slo_report_mock, read_runtime_events_mock):
        read_runtime_events_mock.return_value = [
            {"timestamp": "2026-04-14T10:00:00", "severity": "info", "event_type": "startup", "detail": "started", "context": {}},
            {
                "timestamp": "2026-04-14T10:01:00",
                "severity": "warning",
                "event_type": "spotify_missing",
                "detail": "missing credentials",
                "context": {},
            },
            {"timestamp": "2026-04-14T10:02:00", "severity": "error", "event_type": "groq_error", "detail": "failed", "context": {}},
        ]
        build_slo_report_mock.return_value = {
            "status": "watch",
            "events_seen": 3,
            "warning_count": 1,
            "error_count": 1,
            "recommendation": "Review warnings.",
        }

        snapshot = build_runtime_event_snapshot(limit=10, severity="warning")

        self.assertEqual(len(snapshot["events"]), 1)
        self.assertIn("filter=warning", snapshot["summary"])
        self.assertTrue(snapshot["formatted_events"][0].startswith("[WARNING]"))


if __name__ == "__main__":
    unittest.main()
