import unittest
from urllib.error import URLError

from open_jarvis.integrations.provider_health import build_provider_health_checks, probe_local_llm


class ProviderHealthTests(unittest.TestCase):
    def test_provider_health_reports_rules_mode_without_optional_keys(self):
        checks = build_provider_health_checks({})
        by_id = {item["id"]: item for item in checks}

        self.assertEqual(by_id["provider_groq"]["severity"], "info")
        self.assertEqual(by_id["provider_gemini"]["severity"], "info")
        self.assertEqual(by_id["provider_local_llm"]["severity"], "info")

    def test_provider_health_reports_configured_cloud_keys_without_network_probe(self):
        checks = build_provider_health_checks({"GROQ_API_KEY": "key", "GEMINI_API_KEY": "key"})
        by_id = {item["id"]: item for item in checks}

        self.assertEqual(by_id["provider_groq"]["severity"], "ok")
        self.assertIn("configured", by_id["provider_groq"]["detail"])
        self.assertEqual(by_id["provider_gemini"]["severity"], "ok")

    def test_local_llm_probe_succeeds_with_injected_fetcher(self):
        result = probe_local_llm("http://127.0.0.1:11434", fetcher=lambda url, timeout: object())

        self.assertEqual(result["severity"], "ok")
        self.assertIn("reachable", result["detail"])

    def test_local_llm_probe_reports_unreachable_endpoint(self):
        def failing_fetcher(url, timeout):
            raise URLError("refused")

        result = probe_local_llm("http://127.0.0.1:11434", fetcher=failing_fetcher)

        self.assertEqual(result["severity"], "warning")
        self.assertIn("not reachable", result["detail"])


if __name__ == "__main__":
    unittest.main()
