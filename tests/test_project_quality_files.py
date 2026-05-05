import unittest
from pathlib import Path


class ProjectQualityFilesTests(unittest.TestCase):
    def test_requirements_file_lists_core_runtime_dependencies(self):
        content = Path("requirements.txt").read_text(encoding="utf-8")

        for package in ["groq", "spotipy", "customtkinter", "python-dotenv", "speechrecognition"]:
            self.assertIn(package, content.lower())
        self.assertNotIn("ruff", content.lower())
        self.assertNotIn("pyinstaller", content.lower())

    def test_dev_requirements_file_lists_contributor_tooling(self):
        content = Path("requirements-dev.txt").read_text(encoding="utf-8")

        for package in ["ruff", "pyinstaller", "pytest", "mypy", "coverage"]:
            self.assertIn(package, content.lower())

    def test_ci_workflow_runs_tests_lint_and_health(self):
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn("python -m unittest discover -s tests -q", workflow)
        self.assertIn("python -m pip install -r requirements-dev.txt", workflow)
        self.assertIn("python -m ruff check", workflow)
        self.assertIn("python kontrol.py --no-pause", workflow)
        self.assertIn("Release signing smoke test", workflow)
        self.assertIn("python eval_runner.py --measured --write-artifacts --release-version ci --output-dir exports", workflow)
        self.assertIn("pyinstaller --noconfirm --onefile --windowed --name JARVIS arayuz.py", workflow)
        self.assertIn("python release_build.py --version ci --artifact dist/JARVIS.exe --output-dir release", workflow)
        self.assertIn("python model_installer.py --write-catalog release/model-catalog-ci.json", workflow)
        self.assertIn("release/model-catalog-ci.json", workflow)
        self.assertIn("jarvis-release-artifacts", workflow)
        self.assertIn("actions/upload-artifact", workflow)

    def test_pyproject_defines_ruff_quality_defaults(self):
        content = Path("pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("[tool.ruff]", content)
        self.assertIn("target-version", content)
        self.assertIn("[tool.coverage.run]", content)
        self.assertIn("ui_dialogs.py", content)
        self.assertIn('"build"', content)
        self.assertIn('"dist"', content)
        self.assertIn('"release"', content)

    def test_readme_documents_product_feature_modules(self):
        content = Path("README.md").read_text(encoding="utf-8")

        for module in [
            "onboarding_engine.py",
            "permission_profiles.py",
            "ui_theme.py",
            "ui_components.py",
            "ui_smoke.py",
            "ui_screenshot_regression.py",
            "repo_hygiene.py",
            "plugin_marketplace.py",
            "plugin_signature.py",
            "plugin_state.py",
            "build_plugin_state_audit",
            "privacy_mode.py",
            "plugin_runner.py",
            "offline_profile.py",
            "evaluation_suite.py",
            "eval_runner.py",
            "eval_artifacts.py",
            "compare_eval_artifacts",
            "release_build.py",
            "model_installer.py",
            "build_signed_model_catalog",
            "verify_model_catalog",
            "verify_model_checksum",
        ]:
            self.assertIn(module, content)

    def test_env_example_lists_product_runtime_settings(self):
        content = Path(".env.example").read_text(encoding="utf-8")

        for key in [
            "JARVIS_PERMISSION_PROFILE",
            "JARVIS_PRIVACY_MODE",
            "JARVIS_LOCAL_LLM_URL",
            "JARVIS_AI_MODE",
            "JARVIS_ENABLE_GROQ",
            "JARVIS_ENABLE_SPOTIFY",
            "JARVIS_CPU_SAMPLE_INTERVAL",
            "JARVIS_ACTION_SEQUENCE_DELAY",
            "JARVIS_APP_LAUNCH_DELAY",
            "JARVIS_SCREENSHOT_DELAY",
            "JARVIS_TTS_PROVIDER",
            "JARVIS_PLUGIN_SIGNING_KEY",
            "JARVIS_PLUGIN_SIGNING_KEYS",
        ]:
            self.assertIn(key, content)

        self.assertIn("GROQ_API_KEY=", content)
        self.assertIn("SPOTIFY_CLIENT_ID=", content)
        self.assertIn("SPOTIFY_CLIENT_SECRET=", content)

    def test_security_and_contribution_docs_exist(self):
        security = Path("SECURITY.md").read_text(encoding="utf-8")
        contributing = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
        architecture = Path("docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        threat_model = Path("docs/THREAT_MODEL.md").read_text(encoding="utf-8")

        self.assertIn("Threat model", security)
        self.assertIn("Report a vulnerability", security)
        self.assertIn("Quality gate", contributing)
        self.assertIn("python -m unittest discover -s tests -q", contributing)
        self.assertIn("Data Flow", architecture)
        self.assertIn("Trust Boundaries", threat_model)
        self.assertIn("Signature Verification", Path("docs/PLUGIN_SECURITY.md").read_text(encoding="utf-8"))

    def test_issue_templates_exist_for_next_contributors(self):
        bug = Path(".github/ISSUE_TEMPLATE/bug_report.md").read_text(encoding="utf-8")
        feature = Path(".github/ISSUE_TEMPLATE/feature_request.md").read_text(encoding="utf-8")

        self.assertIn("Expected behavior", bug)
        self.assertIn("Safety impact", feature)

    def test_readme_contains_easy_roadmap_and_comparison(self):
        content = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("Compared With Other Jarvis Projects", content)
        self.assertIn("Easy Roadmap Complete", content)
        self.assertIn("Current Next Roadmap", content)

    def test_public_ui_text_is_english_and_not_mojibake(self):
        files = [
            Path("arayuz.py"),
            Path("ui_onboarding.py"),
            Path("ui_dialogs.py"),
            Path("jarvis_admin.py"),
            Path("jarvis_admin_config.py"),
            Path("haftalik_guncelleme.py"),
            Path("README.md"),
        ]
        forbidden = [chr(0xC3), chr(0xC4), chr(0xC5), chr(0xFFFD), "Neden:", "Yapman gereken"]

        for file_path in files:
            content = file_path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, content, f"{token!r} found in {file_path}")

    def test_ui_theme_exposes_professional_design_tokens(self):
        from ui_theme import build_design_tokens

        tokens = build_design_tokens()

        self.assertEqual(tokens["name"], "Cyber Hologram")
        self.assertEqual(tokens["palette"]["bg"], "#070A12")
        self.assertEqual(tokens["palette"]["surface"], "#0C1322")
        self.assertEqual(tokens["palette"]["line"], "#11304A")
        self.assertEqual(tokens["palette"]["line_soft"], "#1A4564")
        self.assertEqual(tokens["palette"]["cyan"], "#00D7FF")
        self.assertEqual(tokens["palette"]["cyan_soft"], "#4CEBFF")
        self.assertEqual(tokens["palette"]["cyan_hot"], "#89F2FF")
        self.assertEqual(tokens["palette"]["text"], "#D8F6FF")
        self.assertEqual(tokens["palette"]["text_muted"], "#8FB7C8")
        self.assertEqual(tokens["palette"]["text_faint"], "#5F7D8E")
        self.assertEqual(tokens["palette"]["surface_glass"], "#061018")
        self.assertNotIn("purple", " ".join(tokens["palette"].values()).lower())
        self.assertLessEqual(tokens["radius"]["card"], 12)
        self.assertIn("Orbitron", tokens["fonts"]["display"])

    def test_assistant_state_profiles_drive_dashboard_behavior(self):
        from ui_state import ASSISTANT_STATE_ORDER, get_state_profile, infer_state_from_message

        expected_states = ["BOOTING", "STANDBY", "LISTENING", "PROCESSING", "EXECUTING", "SPEAKING", "ERROR", "OFFLINE"]
        self.assertEqual(list(ASSISTANT_STATE_ORDER), expected_states)
        self.assertEqual(get_state_profile("standby").status, "STANDBY - SAY JARVIS")
        self.assertEqual(get_state_profile("listening").status, "LISTENING...")
        self.assertEqual(get_state_profile("processing").title, "PROCESSING")
        self.assertEqual(get_state_profile("executing").accent, "#00FFC6")
        self.assertEqual(get_state_profile("error").accent, "#FF4D6D")
        self.assertGreater(get_state_profile("processing").reactor_speed, get_state_profile("standby").reactor_speed)
        self.assertEqual(infer_state_from_message("Listening started"), "LISTENING")
        self.assertEqual(infer_state_from_message("[VOICE] Wake word detected"), "LISTENING")
        self.assertEqual(infer_state_from_message("[TASK] Executing action: open_browser"), "EXECUTING")
        self.assertEqual(infer_state_from_message("[TASK] Routing command to Groq"), "PROCESSING")
        self.assertEqual(infer_state_from_message("[STATE] OFFLINE - Microphone not detected"), "OFFLINE")
        self.assertEqual(infer_state_from_message("[STATE] ERROR - TTS failed"), "ERROR")
        self.assertEqual(infer_state_from_message("JARVIS: Hello"), "SPEAKING")
        self.assertEqual(infer_state_from_message("[SPEAKING] Speaking started: Hello"), "SPEAKING")
        self.assertEqual(infer_state_from_message("[OK] Command completed"), "STANDBY")
        self.assertEqual(infer_state_from_message("ERROR microphone not detected"), "ERROR")

    def test_log_events_use_professional_terminal_prefixes(self):
        from ui_log_events import EVENT_PREFIXES, infer_log_kind, normalize_log_event

        self.assertEqual(EVENT_PREFIXES["info"], "[INFO]")
        self.assertEqual(EVENT_PREFIXES["voice"], "[VOICE]")
        self.assertEqual(EVENT_PREFIXES["cmd"], "[CMD]")
        self.assertEqual(EVENT_PREFIXES["task"], "[TASK]")
        self.assertEqual(EVENT_PREFIXES["ok"], "[OK]")
        self.assertEqual(EVENT_PREFIXES["error"], "[ERROR]")
        self.assertEqual(normalize_log_event("JARVIS initialized", "system").message, "[INFO] JARVIS initialized")
        self.assertEqual(normalize_log_event("Open Spotify", "user").message, "[CMD] Open Spotify")
        self.assertEqual(infer_log_kind("Listening started"), "voice")
        self.assertEqual(infer_log_kind("Wake word detected"), "voice")
        self.assertEqual(infer_log_kind("You: open spotify"), "cmd")
        self.assertEqual(infer_log_kind("Launching Spotify"), "task")
        self.assertEqual(infer_log_kind("Executing action: open_browser"), "task")
        self.assertEqual(infer_log_kind("Command completed"), "ok")
        self.assertEqual(infer_log_kind("ERROR microphone not detected"), "error")

    def test_ui_smoke_builds_main_window_without_runtime_thread(self):
        from ui_smoke import run_ui_smoke

        result = run_ui_smoke()

        self.assertEqual(result["status"], "ok")
        self.assertIn("JARVIS", result["title"])
        self.assertGreaterEqual(result["widgets"], 1)

    def test_hologram_layout_has_ring_arcs_spokes_and_particles(self):
        from ui_rendering import build_hologram_layout

        layout = build_hologram_layout(520, 330, angle=15)

        self.assertGreaterEqual(len(layout["rings"]), 5)
        self.assertGreaterEqual(len(layout["arcs"]), 12)
        self.assertGreaterEqual(len(layout["spokes"]), 16)
        self.assertGreaterEqual(len(layout["reactor_triads"]), 12)
        self.assertGreaterEqual(len(layout["light_channels"]), 8)
        self.assertIn("labels", layout)
        self.assertEqual(layout["labels"]["top"][2], "ARC REACTOR")
        self.assertGreaterEqual(len(layout["particles"]), 32)

    def test_hologram_labels_stay_inside_canvas(self):
        from ui_rendering import build_hologram_layout

        width = 520
        height = 330
        layout = build_hologram_layout(width, height, angle=15)
        cx, cy = layout["center"]
        outer_ring = layout["rings"][0]

        for x, y, _text in layout["labels"].values():
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x, width)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(y, height)
        self.assertLessEqual(layout["labels"]["top"][1], 6)
        self.assertGreaterEqual(layout["labels"]["bottom"][1], height - 6)
        self.assertLess(layout["labels"]["top"][1], cy - outer_ring)
        self.assertGreater(layout["labels"]["bottom"][1], cy + outer_ring)

    def test_main_ui_keeps_assistant_status_without_control_clutter(self):
        content = Path("arayuz.py").read_text(encoding="utf-8")

        self.assertIn("STANDBY - SAY JARVIS", content)
        self.assertIn('"GPU"', content)
        self.assertIn('"AI"', content)
        self.assertNotIn("WAKE WORD ACTIVE", content)
        self.assertNotIn("CLICK HERE TO SPEAK", content)
        self.assertIn("JARVIS CYBER INTERFACE", content)
        self.assertIn("ALL SYSTEMS OPERATIONAL", content)
        self.assertIn("self.iconify", content)
        self.assertIn("_build_sidebar", content)
        self.assertIn("_show_page", content)
        self.assertIn("build_info_page", content)
        self.assertIn('"dashboard"', content)
        self.assertIn('"system"', content)
        self.assertIn('"modules"', content)
        self.assertIn('"integrations"', content)
        self.assertIn('"security"', content)
        self.assertIn('"settings"', content)
        self.assertIn("_draw_equalizer", content)
        self.assertIn("_draw_background", content)
        self.assertIn("_draw_sidebar_dots", content)
        self.assertIn("_draw_bottom_reactor", content)
        self.assertIn("COMMAND STREAM", content)
        self.assertIn("set_assistant_state", content)
        self.assertIn("get_state_profile", content)
        self.assertIn("normalize_log_event", content)
        self.assertIn("infer_log_kind", content)
        self.assertIn("_signal_phase", content)
        self.assertIn("self.after(90, self._draw_equalizer)", content)
        self.assertIn("self.after(70, self._draw_waveform)", content)
        self.assertIn("self.after(120, self._draw_sidebar_dots)", content)
        for removed_button in ['"SETTINGS"', '"PLUGINS"', '"LOGS"']:
            self.assertNotIn(removed_button, content)

    def test_sidebar_pages_define_phase_three_navigation(self):
        from ui_pages import PAGE_ITEMS, PAGE_TITLES, _build_page_values

        expected_pages = ["dashboard", "system", "modules", "integrations", "security", "settings"]
        self.assertEqual(list(PAGE_TITLES), expected_pages)
        self.assertIn("CPU usage", PAGE_ITEMS["system"])
        self.assertIn("Spotify control", PAGE_ITEMS["modules"])
        self.assertIn("Groq provider", PAGE_ITEMS["integrations"])
        self.assertIn("Safe mode", PAGE_ITEMS["security"])
        self.assertIn("Wake word", PAGE_ITEMS["settings"])
        self.assertIn("CPU usage", _build_page_values("system"))
        self.assertIn("Groq provider", _build_page_values("integrations"))
        self.assertIn("Permission profile", _build_page_values("security"))
        self.assertNotIn("READY FOR PHASE 4 DATA BINDING", Path("ui_pages.py").read_text(encoding="utf-8"))

    def test_ui_screenshot_regression_defines_visual_quality_gate(self):
        content = Path("ui_screenshot_regression.py").read_text(encoding="utf-8")

        self.assertIn("run_screenshot_regression", content)
        self.assertIn("validate_metrics", content)
        self.assertIn("PAGES_TO_CAPTURE", content)
        self.assertIn("MIN_CYAN_PIXELS", content)


if __name__ == "__main__":
    unittest.main()
