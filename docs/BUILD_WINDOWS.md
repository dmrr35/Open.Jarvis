# Build Windows Portable

This guide describes the v0.5.0 portable build preparation workflow. It does not require a real PyInstaller build for tests or dry-runs.

## Dry Run

```powershell
python scripts/build_windows_portable.py --version v0.5.0 --dry-run
```

The dry run prints planned paths and the PyInstaller command. It must not create a final EXE or ZIP.

## Real Build

Run a real build only when you intentionally want local release artifacts:

```powershell
python scripts/build_windows_portable.py --version v0.5.0 --clean
```

The default command uses one-folder PyInstaller mode with `arayuz.py` as the GUI entrypoint. One-folder mode is preferred first because it is easier to inspect, debug, and verify than a self-extracting one-file build.

## Verify Artifacts

```powershell
python scripts/verify_release_artifact.py release/Open.Jarvis-v0.5.0-windows-portable
python scripts/verify_release_artifact.py release/Open.Jarvis-v0.5.0-windows-portable.zip
```

The verifier rejects private data, logs, caches, `.env`, traversal paths, unexpected executables, nested archives, and suspicious secret-like text.

## Cleanup

Generated output is ignored by Git. Before committing source changes, clean local artifacts:

```powershell
python repo_hygiene.py --clean
python repo_hygiene.py
git status --ignored --short
```

Do not commit `build/`, `dist/`, `release/`, EXE files, ZIP files, logs, caches, `.env`, memory data, or generated media.

## Installer Status

Full installer support is future work. Portable ZIP is the safer first distribution format because it avoids admin privileges, registry changes, uninstall logic, and installer signing decisions.
