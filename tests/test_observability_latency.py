import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from open_jarvis.health.observability import build_latency_snapshot, record_latency_metric, record_runtime_event


class ObservabilityLatencyTests(unittest.TestCase):
    def test_record_latency_metric_writes_structured_runtime_event(self):
        with TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "runtime_events.jsonl"
            with patch("open_jarvis.health.observability.EVENT_LOG", event_log):
                record_latency_metric("llm", 123.45, provider="groq", command="open chrome")
                snapshot = build_latency_snapshot()

        self.assertEqual(snapshot["count"], 1)
        self.assertEqual(snapshot["latest"]["context"]["stage"], "llm")
        self.assertEqual(snapshot["latest"]["context"]["provider"], "groq")
        self.assertEqual(snapshot["average_ms"], 123.45)

    def test_record_runtime_event_masks_sensitive_detail_and_context(self):
        with TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "runtime_events.jsonl"
            with patch("open_jarvis.health.observability.EVENT_LOG", event_log):
                record_runtime_event(
                    "secret_test",
                    "GROQ_API_KEY=abc123 failed",
                    context={"api_key": "abc123", "message": "TOKEN=secret", "nested": {"password": "pw"}},
                )
                event = json.loads(event_log.read_text(encoding="utf-8"))

        self.assertEqual(event["detail"], "GROQ_API_KEY=*** failed")
        self.assertEqual(event["context"]["api_key"], "***")
        self.assertEqual(event["context"]["message"], "TOKEN=***")
        self.assertEqual(event["context"]["nested"]["password"], "***")


if __name__ == "__main__":
    unittest.main()
