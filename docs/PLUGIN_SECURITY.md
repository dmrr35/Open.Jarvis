# Plugin Security

Plugins are treated as untrusted by default.

## Trust Model

- New v0.3.0 plugins should use a manifest with `id`, `name`, `version`, `entrypoint`, and `permissions`.
- Legacy manifests with `name`, `version`, `entrypoint`, and `signer` are still supported with compatibility warnings.
- Accept only trusted signers.
- Verify the manifest signature before marketplace trust or enablement.
- Reject entrypoints that escape the plugin directory.
- Build execution through `plugin_runner.py` instead of importing plugin code directly.
- Discovery and registry listing must not execute plugin code.

## Permission Model

Plugin permissions are separate from runtime command permission profiles. Unknown permissions are blocked. High-risk and critical permissions are denied by default unless an explicit local approval policy allows them.

Examples:

- Low risk: `commands.register`, `ui.notify`
- Medium risk: `memory.read`, `memory.write`, `audio.play`, `spotify.control`, `groq.request`
- High risk: `commands.execute`, `network.request`, `filesystem.read`
- Critical: `filesystem.write`, `desktop.automation`, `process.spawn`

Signing a plugin does not grant permissions. Enabling a plugin does not bypass destructive-action safety gates.

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

## Lifecycle and Context

The optional loader supports `on_load`, `on_enable`, `on_disable`, `on_command`, and `on_shutdown` hooks. Hook failures are isolated and reported as plugin failures instead of crashing the assistant.

Plugins receive a `PluginContext` facade. The context does not expose raw environment variables, API keys, provider clients, subprocess access, arbitrary filesystem access, or UI internals. Privileged context APIs require matching permissions.

## Signature Verification

Use `plugin_signature.sign_plugin_manifest(...)` to sign local manifests and `plugin_signature.verify_plugin_signature(...)` to verify them. Local plugin signatures use deterministic JSON plus HMAC-SHA256.

Environment keys:

- `JARVIS_PLUGIN_SIGNING_KEY` maps to the local `ci` signer.
- `JARVIS_PLUGIN_SIGNING_KEYS` can hold signer-to-key JSON for multiple trusted signers.

Do not commit real plugin signing keys. Marketplace trust and plugin enablement should treat unsigned or tampered manifests as blocked.

## Enablement State

Use `plugin_state.enable_plugin(...)` and `plugin_state.disable_plugin(...)` to persist plugin state in `jarvis_plugin_state.json`. Enablement is signature-gated; a plugin with a missing, unknown, or invalid signature stays blocked.

## Validation

Use `plugin_security.validate_plugin_manifest(...)` or the v0.3.0 manifest validator before loading a plugin, and keep plugin execution behind explicit user trust decisions.
