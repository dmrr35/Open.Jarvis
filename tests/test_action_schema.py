import unittest

from open_jarvis.commands.action_schema import validate_action_payload


class ActionSchemaTests(unittest.TestCase):
    def test_accepts_valid_single_action(self):
        result = validate_action_payload({"action": "get_time", "params": {}, "response": "At once, sir."})

        self.assertTrue(result.valid)
        self.assertEqual(result.reason, "")

    def test_accepts_valid_multi_action(self):
        result = validate_action_payload({"actions": [{"action": "get_time", "params": {}}, {"action": "get_date"}]})

        self.assertTrue(result.valid)

    def test_rejects_non_dict_payload(self):
        result = validate_action_payload("get_time")

        self.assertFalse(result.valid)
        self.assertIn("object", result.reason)

    def test_rejects_missing_action_name(self):
        result = validate_action_payload({"params": {}})

        self.assertFalse(result.valid)
        self.assertIn("action", result.reason)

    def test_rejects_non_dict_params(self):
        result = validate_action_payload({"action": "get_time", "params": []})

        self.assertFalse(result.valid)
        self.assertIn("params", result.reason)


if __name__ == "__main__":
    unittest.main()
