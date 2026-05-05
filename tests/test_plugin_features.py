from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from plugin_marketplace import build_marketplace
from plugin_runner import build_plugin_execution_plan, run_plugin_in_sandbox
from plugin_signature import sign_plugin_manifest, verify_plugin_signature
from plugin_state import build_plugin_state, build_plugin_state_audit, disable_plugin, enable_plugin


class PluginFeaturesTest(TestCase):
    def test_plugin_marketplace_scores_trusted_and_untrusted_plugins(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            trusted = tmp_path / "trusted"
            trusted.mkdir()
            signed_manifest = {
                "name": "Lights",
                "version": "1.0",
                "entrypoint": "main.py",
                "signer": "ci",
                "description": "controls lights",
            }
            signed_manifest["signature"] = sign_plugin_manifest(signed_manifest, signing_key="k" * 16)["signature"]
            (trusted / "main.py").write_text("print('lights')\n", encoding="utf-8")
            (trusted / "plugin.json").write_text(
                __import__("json").dumps(signed_manifest),
                encoding="utf-8",
            )
            untrusted = tmp_path / "untrusted"
            untrusted.mkdir()
            (untrusted / "plugin.json").write_text(
                '{"name":"Risky","version":"1.0","entrypoint":"../escape.py","signer":"unknown"}',
                encoding="utf-8",
            )

            market = build_marketplace(tmp_path, trusted_signers=["ci"], signing_keys={"ci": "k" * 16})

        self.assertEqual(market["summary"]["total"], 2)
        self.assertEqual(market["plugins"][0]["trust_status"], "trusted")
        self.assertEqual(market["plugins"][0]["signature_status"], "valid")
        self.assertEqual(market["plugins"][0]["sandbox_status"], "ready")
        self.assertEqual(market["plugins"][0]["approval_action"]["action"], "enable")
        self.assertEqual(market["plugins"][1]["trust_status"], "blocked")
        self.assertEqual(market["plugins"][1]["approval_action"]["action"], "blocked")

    def test_plugin_marketplace_handles_malformed_manifest(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plugin = tmp_path / "broken"
            plugin.mkdir()
            (plugin / "plugin.json").write_text("{not-json", encoding="utf-8")

            market = build_marketplace(tmp_path, trusted_signers=["ci"])

        self.assertEqual(market["summary"]["blocked"], 1)
        self.assertTrue(market["plugins"][0]["issues"])

    def test_plugin_signature_rejects_tampered_manifests(self):
        manifest = {"name": "Lights", "version": "1", "entrypoint": "main.py", "signer": "ci"}
        signed = sign_plugin_manifest(manifest, signing_key="k" * 16)

        trusted = verify_plugin_signature(signed["manifest"], signing_keys={"ci": "k" * 16})
        tampered_manifest = dict(signed["manifest"], entrypoint="evil.py")
        tampered = verify_plugin_signature(tampered_manifest, signing_keys={"ci": "k" * 16})

        self.assertTrue(trusted["valid"])
        self.assertFalse(tampered["valid"])
        self.assertEqual(tampered["status"], "invalid")

    def test_plugin_state_enable_disable_is_persistent_and_signature_gated(self):
        with TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "plugin_state.json"
            manifest = {"name": "Lights", "version": "1", "entrypoint": "main.py", "signer": "ci"}
            signed = sign_plugin_manifest(manifest, signing_key="k" * 16)["manifest"]

            enabled = enable_plugin("Lights", signed, state_file=state_file, signing_keys={"ci": "k" * 16})
            disabled = disable_plugin("Lights", state_file=state_file)
            state = build_plugin_state(state_file=state_file)

        self.assertEqual(enabled["status"], "enabled")
        self.assertEqual(disabled["status"], "disabled")
        self.assertFalse(state["plugins"]["Lights"]["enabled"])

    def test_plugin_state_records_approval_and_audit_events(self):
        with TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "plugin_state.json"
            manifest = {"name": "Lights", "version": "1", "entrypoint": "main.py", "signer": "ci"}
            signed = sign_plugin_manifest(manifest, signing_key="k" * 16)["manifest"]

            enabled = enable_plugin(
                "Lights",
                signed,
                state_file=state_file,
                signing_keys={"ci": "k" * 16},
                approved_by="local-admin",
                approval_reason="trusted local test plugin",
            )
            disable_plugin("Lights", state_file=state_file, approved_by="local-admin", approval_reason="maintenance")
            audit = build_plugin_state_audit(state_file=state_file)

        self.assertEqual(enabled["approval"]["approved_by"], "local-admin")
        self.assertEqual([event["action"] for event in audit["events"]], ["enable", "disable"])
        self.assertTrue(all(event["approved_by"] == "local-admin" for event in audit["events"]))

    def test_plugin_execution_plan_enforces_isolated_entrypoints(self):
        with TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp)
            (plugin_dir / "main.py").write_text("print('ok')", encoding="utf-8")

            manifest = {"name": "Lights", "version": "1", "entrypoint": "main.py", "signer": "ci"}
            signed = sign_plugin_manifest(manifest, signing_key="k" * 16)["manifest"]
            allowed = build_plugin_execution_plan(plugin_dir, signed, trusted_signers=["ci"], signing_keys={"ci": "k" * 16})
            blocked = build_plugin_execution_plan(
                plugin_dir, {"name": "Escape", "version": "1", "entrypoint": "../main.py", "signer": "ci"}
            )

        self.assertEqual(allowed["status"], "ready")
        self.assertEqual(allowed["execution"]["mode"], "subprocess")
        self.assertEqual(blocked["status"], "blocked")

    def test_plugin_sandbox_runs_in_temporary_workspace_and_cleans_up(self):
        with TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "plugin"
            plugin_dir.mkdir()
            (plugin_dir / "main.py").write_text(
                "from pathlib import Path\nPath('marker.txt').write_text('sandboxed', encoding='utf-8')\nprint('plugin ok')\n",
                encoding="utf-8",
            )
            manifest = {"name": "Lights", "version": "1", "entrypoint": "main.py", "signer": "ci"}
            signed = sign_plugin_manifest(manifest, signing_key="k" * 16)["manifest"]

            result = run_plugin_in_sandbox(plugin_dir, signed, trusted_signers=["ci"], signing_keys={"ci": "k" * 16})
            workspace_path = Path(result["workspace"]["path"])

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["returncode"], 0)
        self.assertIn("plugin ok", result["stdout"])
        self.assertFalse((plugin_dir / "marker.txt").exists())
        self.assertTrue(result["workspace"]["deleted"])
        self.assertFalse(workspace_path.exists())
        self.assertTrue(result["resource_limits"]["job_object"]["enabled"])

    def test_plugin_sandbox_times_out_and_reports_error_without_leaking_workspace(self):
        with TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "plugin"
            plugin_dir.mkdir()
            (plugin_dir / "main.py").write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
            manifest = {"name": "Slow", "version": "1", "entrypoint": "main.py", "signer": "ci"}
            signed = sign_plugin_manifest(manifest, signing_key="k" * 16)["manifest"]

            result = run_plugin_in_sandbox(
                plugin_dir,
                signed,
                trusted_signers=["ci"],
                signing_keys={"ci": "k" * 16},
                timeout_seconds=0.1,
            )
            workspace_path = Path(result["workspace"]["path"])

        self.assertEqual(result["status"], "timeout")
        self.assertIn("timed out", result["error"])
        self.assertTrue(result["workspace"]["deleted"])
        self.assertFalse(workspace_path.exists())
