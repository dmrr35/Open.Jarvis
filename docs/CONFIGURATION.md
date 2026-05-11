# Configuration

Open.Jarvis v0.6.0 adds a central configuration manager for non-secret settings while preserving the existing `.env` and environment variable workflow.

## Precedence

Configuration is resolved deterministically:

1. Built-in safe defaults.
2. Existing environment variables, including values loaded by legacy `.env` flows.
3. User `settings.json` for non-secret settings.
4. Explicit Settings UI saves, which update `settings.json`.

`.env.example` is documentation only. It is never used as runtime secret storage.

## Storage Locations

Source/development mode stores non-secret settings in the current user's local application data directory under `Open.Jarvis/settings.json`.

Portable mode stores non-secret settings in the portable package's `config/settings.json` when the user explicitly saves settings. Real `config/settings.json` files are local user data and must not be included in public source releases or portable ZIPs.

Tests use injected temporary paths and must not touch real user settings.

## Secret Policy

Raw secrets remain environment-only. Do not store these in `settings.json`:

- `GROQ_API_KEY`
- `SPOTIFY_CLIENT_SECRET`
- access or refresh tokens
- `GEMINI_API_KEY`
- release signing keys
- plugin signing keys
- any API key, secret, token, password, bearer, authorization, private key, or signing key

The Settings UI and diagnostics expose only status values such as `configured` or `missing`.

## Validation

The configuration manager validates types, allowed values, numeric ranges, boolean strings, and unknown fields. Invalid individual values fall back to safe defaults and produce warnings. Missing or corrupted config files do not block startup.

## Recovery

If settings become invalid, use the Settings UI reset action or delete the local `settings.json`. Open.Jarvis will continue with built-in defaults plus environment variables.

## Safe Export

`ConfigManager.export_safe()` returns resolved non-secret settings, diagnostics, and masked secret status. It never exports raw API keys, OAuth secrets, tokens, or signing keys.

## Not Implemented

v0.6.0 does not add encrypted secret storage, cloud sync, installer-managed settings, a database, or admin-required configuration.
