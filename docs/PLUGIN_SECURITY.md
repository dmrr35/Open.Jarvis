# Plugin Security

Plugins are treated as untrusted by default.

## Trust Model

- Require a manifest with `name`, `version`, `entrypoint`, and `signer`.
- Accept only trusted signers.
- Verify the manifest signature before marketplace trust or enablement.
- Reject entrypoints that escape the plugin directory.
- Build execution through `plugin_runner.py` instead of importing plugin code directly.

## Sandbox Policy

Default policy is conservative:

- isolated execution
- network restricted
- filesystem scoped
- no process spawning
- memory and timeout caps

## Execution Planning

Use `plugin_runner.build_plugin_execution_plan(...)` after manifest validation. The plan returns `blocked` with issues for unsafe plugins, or `ready` with a bounded subprocess command, working directory, timeout, and sanitized environment for trusted plugins.

## Real Sandbox Execution

Use `plugin_runner.run_plugin_in_sandbox(...)` for trusted plugins that should actually run. The runner:

- reuses manifest and signature validation before execution
- copies the plugin into a per-run temporary workspace
- runs the plugin entrypoint as a subprocess with sanitized environment variables
- captures stdout and stderr for audit/debug output
- applies timeout and resource policy metadata
- removes the temporary workspace after success, failure, or timeout

The marketplace exposes sandbox readiness and approval action metadata so users can see whether a plugin is safe to enable before any execution path is used.

## Signature Verification

Use `plugin_signature.sign_plugin_manifest(...)` to sign local manifests and `plugin_signature.verify_plugin_signature(...)` to verify them. Local plugin signatures use deterministic JSON plus HMAC-SHA256.

Environment keys:

- `JARVIS_PLUGIN_SIGNING_KEY` maps to the local `ci` signer.
- `JARVIS_PLUGIN_SIGNING_KEYS` can hold signer-to-key JSON for multiple trusted signers.

Do not commit real plugin signing keys. Marketplace trust and plugin enablement should treat unsigned or tampered manifests as blocked.

## Enablement State

Use `plugin_state.enable_plugin(...)` and `plugin_state.disable_plugin(...)` to persist plugin state in `jarvis_plugin_state.json`. Enablement is signature-gated; a plugin with a missing, unknown, or invalid signature stays blocked.

## Validation

Use `plugin_security.validate_plugin_manifest(...)` before loading a plugin, and keep plugin execution behind explicit user trust decisions.
