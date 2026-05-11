# Settings UI

The v0.6.0 Settings UI is a minimal, schema-backed surface for safe local configuration.

## What It Edits

The UI edits non-secret settings such as theme, language, AI mode flags, wake word, voice toggles, plugin mode, Spotify enablement, redirect URI, privacy mode, and runtime safety options.

Saved values go through `ConfigManager` validation and are written to the user's local `settings.json` with an atomic replace.

## What It Does Not Edit

The UI does not display or save raw secrets. API keys, OAuth client secrets, tokens, release signing keys, and plugin signing keys remain environment-only. Secret rows show masked presence status only.

## Error Handling

If config loading fails, the UI falls back to defaults and diagnostics. If validation fails during save, the UI reports the error and does not write partial settings.

Runtime-sensitive values may require restarting Open.Jarvis because some legacy modules still read environment values at import time.

## Source And Portable Modes

Source mode uses a user-local config directory. Portable mode uses the package-local `config` folder only when the user saves settings. Real settings files are private user data and must not be shipped in public packages.
