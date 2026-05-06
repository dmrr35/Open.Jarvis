"""Domain-focused product tests split from the former monolithic product feature suite."""

from unittest import TestCase

from open_jarvis.evaluation.performance_benchmarks import build_performance_budget, summarize_benchmark_results
from open_jarvis.health.feature_quality import build_feature_catalog, build_feature_quality_report, render_feature_quality_report
from open_jarvis.release.maintenance import build_maintenance_plan


class ProductQualityMaintenanceTest(TestCase):
    def test_maintenance_plan_recommends_safe_cleanup_actions(self):
        plan = build_maintenance_plan({"log_bytes": 2_000_000, "memory_score": 40, "cache_bytes": 3_000_000})

        self.assertEqual([item["id"] for item in plan["actions"]], ["prune_memory", "rotate_logs", "trim_cache"])
        self.assertTrue(all(item["safe"] for item in plan["actions"]))

    def test_maintenance_plan_stays_empty_when_metrics_are_healthy(self):
        plan = build_maintenance_plan({"log_bytes": 10, "memory_score": 90, "cache_bytes": 10})

        self.assertEqual(plan["actions"], [])

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
