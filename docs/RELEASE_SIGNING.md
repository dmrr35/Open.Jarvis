# Release Signing

JARVIS release signing uses a trusted-signer model with HMAC verification. CI now includes a release signing smoke test so the policy is exercised automatically instead of living only as documentation.

## Configuration

- `JARVIS_RELEASE_SIGNING_KEY` stores the HMAC secret.
- `release_security.json` stores the trusted signer list and key policy.
- `release_security.validate_release_environment(...)` verifies key length, trusted signers, and signature-required posture without printing secrets.
- `release_security.build_key_rotation_plan(...)` reports whether the signing key is current, near rotation, or overdue.

## Workflow

1. Build a deterministic release manifest with `build_release_manifest(...)`.
2. Sign the payload with `sign_release_payload(...)`.
3. Verify the payload with `verify_release_signature(...)`.
4. Run the CI smoke check before publishing artifacts.

## Safety Notes

- Rotate the signing key regularly.
- Keep the key out of source control.
- Reject signatures from untrusted signers.
- Never log the signing key or derived secret material.
