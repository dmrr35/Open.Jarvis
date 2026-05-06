"""Domain-focused product tests split from the former monolithic product feature suite."""

from unittest import TestCase

from open_jarvis.runtime.e2e_readiness import build_e2e_readiness_plan
from open_jarvis.runtime.onboarding_engine import build_onboarding_result
from open_jarvis.runtime.workflow_engine import build_workflow_plan


class ProductOnboardingWorkflowTest(TestCase):
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

    def test_workflow_plan_turns_steps_into_safe_executable_plan(self):
        plan = build_workflow_plan("research", ["search topic", "summarize", "save notes"])

        self.assertEqual(plan["status"], "ready")
        self.assertEqual([step["order"] for step in plan["steps"]], [1, 2, 3])
        self.assertTrue(all(step["rollback"] for step in plan["steps"]))

    def test_workflow_plan_handles_empty_steps(self):
        plan = build_workflow_plan("empty", ["", "   "])

        self.assertEqual(plan["status"], "empty")
        self.assertEqual(plan["steps"], [])

    def test_e2e_readiness_plan_covers_critical_desktop_flows(self):
        plan = build_e2e_readiness_plan(["ui_start", "voice_command", "onboarding", "permission_profile"])

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["coverage_target"], "desktop-critical")
        self.assertEqual(len(plan["flows"]), 4)
