# Security Policy

## Threat model

Open.Jarvis can listen to voice commands, open applications, control the desktop, read clipboard text, use API keys, and persist memory. The main risks are accidental destructive actions, credential exposure, unsafe plugins, prompt injection, over-broad desktop automation, and untrusted release artifacts.

## Current safety defaults

- Destructive runtime actions are blocked unless `JARVIS_ALLOW_DESTRUCTIVE_ACTIONS=true`.
- Browser navigation is limited to `http` and `https` URLs.
- Plugin manifests must keep entrypoints inside the plugin directory.
- Plugin discovery must not execute plugin code.
- Plugin permissions are deny-by-default for unknown, high-risk, and critical capabilities.
- Privacy mode can disable memory writes and mask secret-like values.
- Release signing uses trusted signers and a signing key policy.
- Health checks surface missing credentials before normal runtime use.
- Public release checks treat signing as optional for source releases, but signed executable/model artifacts should use a trusted signing key.

## Secret and environment rules

- Keep real credentials only in a local `.env` file.
- Commit `.env.example` with placeholders only.
- Keep `settings.json` limited to non-secret preferences. The v0.6.0 Settings UI shows secret presence only and does not store raw API keys, OAuth secrets, tokens, or signing keys.
- Run `python repo_hygiene.py --include-secrets` before publishing.
- Run `python repo_hygiene.py --clean` to remove generated artifacts; add `--include-secrets` only after backing up or rotating local keys.
- Do not paste API keys, OAuth tokens, Spotify secrets, plugin signing keys, release signing keys, runtime logs, or JSONL event streams into issues.
- Do not paste private plugin manifests if they contain local paths, internal package names, or signing metadata.
- Logs and UI messages should mask secret-like values instead of printing raw credentials.

## Report a vulnerability

Do not publish exploit details in a public issue. Create a private report or contact the maintainer directly with:

- Affected file or feature.
- Steps to reproduce.
- Expected and actual impact.
- Whether secrets, files, desktop control, or external services are involved.
- Suggested mitigation if known.

## Supported versions

This project is pre-release. Treat the current main workspace as the only supported development version until tagged releases are published.

## Secure development checklist

- Add or update tests for every security-sensitive behavior.
- Run `python -m unittest discover -s tests -q`.
- Run `python -m ruff check .` and `python -m mypy .`.
- Run `python project_audit.py`.
- Never commit `.env`, API keys, tokens, generated secrets, or local user data.
- Never commit real `config/settings.json` files from source or portable runs.
- Prefer allowlists over blocklists for commands, plugins, and URLs.
- Add negative tests for plugin permissions, broken plugin hooks, and invalid manifests.

## Out of scope

- Support for user-modified plugins that bypass the trust policy.
- Systems running with intentionally disabled safety gates.
- Secrets leaked outside the repository by local tools or shell history.
