import unittest

from runtime import ui_bridge


class UiBridgeTest(unittest.TestCase):
    def setUp(self):
        ui_bridge.set_ui_callback(None)

    def test_send_log_calls_registered_callback(self):
        events = []

        ui_bridge.set_ui_callback(events.append)
        ui_bridge.send_log("hello")

        self.assertEqual(events, ["hello"])

    def test_send_log_records_structured_runtime_event(self):
        recorded = []

        ui_bridge.send_log("[ERROR] Microphone not detected", record_event=recorded.append)

        self.assertEqual(recorded[0]["event_type"], "ui_log")
        self.assertEqual(recorded[0]["detail"], "[ERROR] Microphone not detected")
        self.assertEqual(recorded[0]["severity"], "error")

    def test_send_state_notifies_ui_and_records_event(self):
        events = []
        recorded = []

        ui_bridge.set_ui_callback(events.append)
        ui_bridge.send_state("LISTENING", "Wake word detected", record_event=recorded.append)

        self.assertEqual(events, ["[STATE] LISTENING - Wake word detected"])
        self.assertEqual(recorded[0]["event_type"], "ui_state")
        self.assertEqual(recorded[0]["context"]["state"], "LISTENING")

    def test_send_metric_records_metric_and_optional_ui_line(self):
        events = []
        recorded = []

        ui_bridge.set_ui_callback(events.append)
        ui_bridge.send_metric("latency", 42.5, unit="ms", publish=True, record_event=recorded.append)

        self.assertEqual(events, ["[METRIC] latency=42.5ms"])
        self.assertEqual(recorded[0]["event_type"], "ui_metric")
        self.assertEqual(recorded[0]["context"]["metric"], "latency")


if __name__ == "__main__":
    unittest.main()
