# Threat Model

## Trust Boundaries

| Boundary | Risk | Control |
|---|---|---|
| Voice input to command routing | Misheard or malicious commands | Wake word, permission profiles, destructive action gates |
| Command routing to desktop actions | Unsafe system operations | `runtime_safety.py`, action allow/block policy |
| User URLs to browser | Local file or unsafe scheme launch | `url_safety.py` allows only HTTP and HTTPS |
| Plugins to runtime | Supply-chain or path traversal abuse | Manifest validation, trusted signers, scoped entrypoints |
| Release artifact to updater | Tampered binaries | HMAC signing policy and CI smoke verification |
| Logs and UI output | Secret exposure | Privacy mode and secret masking helpers |

## Priority Threats

1. Destructive desktop actions triggered by mistake.
2. Malicious plugin manifests or entrypoints.
3. Unsigned or tampered release artifacts.
4. Secrets leaked through logs, UI, or reports.
5. Unsafe local file paths or URL schemes.

## Required Controls

- Destructive actions must remain blocked unless explicitly enabled.
- Plugin entrypoints must stay inside their plugin directory.
- Release builds must include signed manifests.
- Health checks must not print secret values.
- Runtime events should mask sensitive values before persistence.
