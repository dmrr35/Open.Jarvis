from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from open_jarvis.health.health_center import apply_health_fix, apply_safe_health_fixes, build_health_center, rotate_logs


class HealthCenterTests(TestCase):
    def test_health_center_prioritizes_checks_and_adds_fix_commands(self):
        center = build_health_center(
            [
                {"id": "groq", "severity": "critical", "title": "Groq", "fix": "Add key"},
                {"id": "spotify", "severity": "warning", "title": "Spotify", "fix": "Add credentials"},
                {"id": "memory", "severity": "info", "title": "Memory", "fix": "Prune"},
            ]
        )

        self.assertEqual([item["id"] for item in center["checks"]], ["groq", "spotify", "memory"])
        self.assertEqual(center["checks"][0]["fix_command"], "python kontrol.py --no-pause")

    def test_health_center_marks_only_safe_one_click_fixes_available(self):
        center = build_health_center(
            [
                {"id": "memory", "severity": "info", "title": "Memory", "fix": "Prune"},
                {"id": "runtime", "severity": "warning", "title": "Runtime", "fix": "Review warnings"},
                {"id": "spotify", "severity": "warning", "title": "Spotify", "fix": "Add credentials"},
            ]
        )
        by_id = {item["id"]: item for item in center["checks"]}

        self.assertTrue(by_id["memory"]["fix_plan"]["available"])
        self.assertEqual(by_id["memory"]["fix_plan"]["mode"], "safe")
        self.assertEqual(by_id["runtime"]["fix_plan"]["fix_id"], "rotate_logs")
        self.assertFalse(by_id["spotify"]["fix_plan"]["available"])
        self.assertEqual(center["summary"]["safe_fixes"], 2)

    def test_apply_health_fix_supports_dry_run_and_injected_safe_handler(self):
        calls = []
        dry_run = apply_health_fix("prune_memory", dry_run=True, handlers={"prune_memory": lambda: calls.append("applied")})
        applied = apply_health_fix("prune_memory", dry_run=False, handlers={"prune_memory": lambda: calls.append("applied")})

        self.assertEqual(dry_run["status"], "dry_run")
        self.assertEqual(applied["status"], "applied")
        self.assertEqual(calls, ["applied"])

    def test_apply_health_fix_records_dry_run_apply_and_unsupported_events(self):
        events = []

        def recorder(event_type, detail, severity="info", context=None):
            events.append({"event_type": event_type, "detail": detail, "severity": severity, "context": context or {}})

        apply_health_fix("prune_memory", dry_run=True, handlers={"prune_memory": lambda: None}, event_recorder=recorder)
        apply_health_fix("prune_memory", dry_run=False, handlers={"prune_memory": lambda: None}, event_recorder=recorder)
        apply_health_fix("unknown", dry_run=False, handlers={"prune_memory": lambda: None}, event_recorder=recorder)

        self.assertEqual([event["event_type"] for event in events], ["health_fix_dry_run", "health_fix_applied", "health_fix_unsupported"])
        self.assertEqual(events[0]["context"]["fix_id"], "prune_memory")
        self.assertTrue(events[0]["context"]["dry_run"])
        self.assertFalse(events[1]["context"]["dry_run"])
        self.assertEqual(events[2]["severity"], "warning")

    def test_apply_safe_health_fixes_skips_manual_items(self):
        center = build_health_center(
            [
                {"id": "memory", "severity": "info", "title": "Memory", "fix": "Prune"},
                {"id": "spotify", "severity": "warning", "title": "Spotify", "fix": "Add credentials"},
            ]
        )

        result = apply_safe_health_fixes(center, dry_run=True)

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["fix_id"], "prune_memory")

    def test_apply_safe_health_fixes_forwards_event_recorder(self):
        events = []
        center = build_health_center([{"id": "memory", "severity": "info", "title": "Memory", "fix": "Prune"}])

        apply_safe_health_fixes(
            center,
            dry_run=True,
            handlers={"prune_memory": lambda: None},
            event_recorder=lambda event_type, detail, severity="info", context=None: events.append(event_type),
        )

        self.assertEqual(events, ["health_fix_dry_run"])

    def test_rotate_logs_archives_existing_log_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            event_log = root / "runtime_events.jsonl"
            app_log = root / "jarvis.log"
            event_log.write_text("event\n", encoding="utf-8")
            app_log.write_text("app\n", encoding="utf-8")

            result = rotate_logs([event_log, app_log], timestamp="20260503T001500")
            archived_paths = [Path(item["archive"]) for item in result["rotated"]]

        self.assertEqual(result["status"], "rotated")
        self.assertEqual(len(archived_paths), 2)
        self.assertTrue(all(path.name.endswith(".20260503T001500.bak") for path in archived_paths))
