# Windows Portable Package

Open.Jarvis v0.5.0 prepares a portable ZIP workflow for Windows. The portable package is additive: source installation with `python arayuz.py`, `python jarvis.py`, and `python -m open_jarvis.app.main` remains supported.

## What The Portable Package Contains

A verified portable package is expected to contain:

```text
Open.Jarvis-vX.Y.Z-windows-portable/
+-- Open.Jarvis/
|   +-- Open.Jarvis.exe
|   `-- _internal/
+-- README_FIRST.txt
+-- LICENSE
+-- .env.example
+-- docs/
+-- plugins/
+-- config/
`-- optional_models/
```

The package must not include `.env`, API keys, Spotify credentials, signing keys, logs, private memory, caches, generated screenshots, generated audio, local runtime files, or large optional model archives.

## First Run

1. Extract the ZIP to a normal user-writable folder.
2. Run `Open.Jarvis/Open.Jarvis.exe`.
3. Keep the app keyless if you only want local commands.
4. Copy `.env.example` to `.env` only when you want optional Groq, Spotify, local LLM, voice, or offline STT configuration.

## Optional Integrations

Groq, Spotify, plugins, microphone input, speaker/TTS output, and offline Vosk models are optional. Missing credentials or missing hardware should degrade gracefully instead of blocking startup.

## SmartScreen Warning

Portable builds are unsigned unless release notes explicitly say otherwise. Windows SmartScreen may warn that the app is from an unknown publisher. That warning is expected for unsigned community builds and is not the same as HMAC release metadata verification.

## Privacy

Do not share `.env`, `logs/`, `memory.json`, screenshots, generated audio, token files, or local config in GitHub issues. Run the artifact verifier before publishing any ZIP.
