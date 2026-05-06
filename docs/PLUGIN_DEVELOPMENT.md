# Plugin Development

Open.Jarvis plugins are local, optional, and disabled unless the local state explicitly enables them. The plugin system is designed for safe local extension first; v0.3.0 does not include an online marketplace or remote plugin catalog.

## Folder Layout

```text
plugins/
`-- example_plugin/
    +-- plugin.json
    `-- main.py
```

Discovery reads `plugins/*/plugin.json` only. It must not import or execute plugin code.

## Manifest

New v0.3.0 manifests should include:

```json
{
  "id": "example_plugin",
  "name": "Example Plugin",
  "version": "0.1.0",
  "description": "Example plugin for Open.Jarvis",
  "author": "community",
  "entrypoint": "main.py",
  "permissions": ["commands.register", "ui.notify"],
  "requires": {
    "open_jarvis": ">=0.3.0"
  },
  "enabled_by_default": false,
  "signer": "ci",
  "signature": "..."
}
```

Rules:

- `id` must be a lowercase safe identifier.
- `entrypoint` must be a relative `.py` file inside the plugin directory.
- `permissions` must be a list of known permissions.
- Unknown permissions are blocked.
- High-risk and critical permissions require explicit approval policy.
- Legacy manifests without `id` can be listed with warnings, but new plugins should use `id`.

## Permissions

Supported plugin permissions:

| Permission | Risk |
|---|---|
| `commands.register` | low |
| `commands.execute` | high |
| `ui.notify` | low |
| `memory.read` | medium |
| `memory.write` | medium |
| `audio.play` | medium |
| `network.request` | high |
| `filesystem.read` | high |
| `filesystem.write` | critical |
| `spotify.control` | medium |
| `groq.request` | medium |
| `desktop.automation` | critical |
| `process.spawn` | critical |

Signing a plugin does not grant permissions. Enabling a plugin does not bypass runtime safety gates.

## Lifecycle Hooks

Plugins may define these hooks:

```python
def on_load(context): ...
def on_enable(context): ...
def on_disable(context): ...
def on_command(command, context): ...
def on_shutdown(context): ...
```

Hook failures are isolated. A broken plugin is marked failed and must not crash the assistant or stop other plugins.

## Plugin Context

`PluginContext` exposes a small permission-gated API:

- `has_permission(permission)`
- `require_permission(permission)`
- `notify(message, level="info")`
- `register_command(name, metadata=None, handler=None)`
- safe stub methods for memory, provider, and filesystem requests

It does not expose raw environment variables, API keys, Groq or Spotify clients, the raw memory store, subprocess access, arbitrary filesystem access, network clients, or UI internals.

## Local Testing

Use temporary plugin folders in tests. Do not require network, real API keys, microphone, speaker, or desktop automation. Invalid manifests, duplicate IDs, unknown permissions, and broken plugin hooks should be tested as blocked or failed states.
