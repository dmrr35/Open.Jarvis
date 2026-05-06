"""Domain-focused product tests split from the former monolithic product feature suite."""

from unittest import TestCase

from open_jarvis.commands.command_history import CommandHistory
from open_jarvis.commands.command_suggestions import suggest_commands
from open_jarvis.commands.error_messages import build_user_error
from open_jarvis.integrations.llm_fallback import build_provider_result, resolve_ai_mode, select_llm_provider


class ProductCommandProviderTest(TestCase):
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

    def test_suggestions_follow_context_and_security_mode(self):
        suggestions = suggest_commands({"last_action": "music", "permission_profile": "safe", "missing": ["spotify"]})

        self.assertEqual(suggestions[0]["command"], "finish spotify setup")
        self.assertTrue(any(item["category"] == "music" for item in suggestions))
        self.assertTrue(all("shutdown" not in item["command"] for item in suggestions))

    def test_suggestions_include_runtime_option_outside_safe_mode(self):
        suggestions = suggest_commands({"permission_profile": "normal"})

        self.assertTrue(any(item["category"] == "runtime" for item in suggestions))

    def test_error_messages_use_reason_and_action_format(self):
        message = build_user_error("Spotify failed", reason="Credentials are missing", fix="Finish Spotify setup")

        self.assertIn("Reason: Credentials are missing", message)
        self.assertIn("Next step: Finish Spotify setup", message)
