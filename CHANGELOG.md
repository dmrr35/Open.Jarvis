# Changelog

All notable changes to J.A.R.V.I.S will be documented in this file.

The format follows Keep a Changelog, and this project uses semantic versioning once tagged releases begin.

## Unreleased

### Added

- Added an MIT license for public open-source distribution.
- Added a public roadmap with feature gaps, missing features, difficulty groups, and implementation phases.
- Added an open-source readiness audit check for required public repository files.
- Added a pull request template for safer community contributions.
- Added a code of conduct for public collaboration.
- Added provider health checks for Groq, Gemini, and optional local LLM endpoints.
- Added privacy masking for runtime event details and structured context before disk writes.
- Added active permission profile visibility to the desktop cockpit.
- Added Health Center safe repair plans with dry-run and apply actions for allowlisted local fixes.
- Added masked runtime audit events for Health Center dry-run, apply, and unsupported repair attempts.
- Added safe Health Center log rotation for runtime posture warnings.
- Redesigned the desktop shell into a black cyber hologram JARVIS interface with a central figure, large title, and primary speak control.
- Reworked the central hologram into a circular HUD ring with rotating arcs, radial ticks, spokes, pulse core, and particles.
- Polished the UI into a larger arc-reactor-focused cockpit with inner triads, light channels, stronger glow rings, and tighter bottom telemetry.
- Replaced the misleading press-to-talk control with a wake-word status panel and moved reactor labels outside the core.
- Added an optimization workflow document with scan baselines, latency targets, UI performance work, memory cleanup, and release gates.
- Added GPU telemetry to the cockpit status strip while keeping Groq AI visibility.
- Added premium HUD depth effects, sidebar pulse dots, terminal corner accents, and animated mini-reactor details.
- Added dashboard assistant state profiles for booting, standby, listening, processing, executing, speaking, error, and offline modes.
- Added structured command stream events with `[INFO]`, `[VOICE]`, `[CMD]`, `[TASK]`, `[OK]`, `[WARN]`, and `[ERROR]` prefixes.
- Added sidebar navigation for Dashboard, System Monitor, Modules, Integrations, Security, and Settings pages.
- Added live secondary page data for system telemetry, module readiness, integrations, security, and settings.
- Added runtime lifecycle UI events for listening, routing, executing, speaking, completion, and failure states.
- Added screenshot regression checks for core cockpit pages to catch blank or visually broken UI renders.
- Added public release readiness reporting for docs, local hygiene, quality gates, and signing readiness.
- Added repository hygiene and public release commands for GitHub publication preparation.
- Added recursive hygiene scanning for generated artifacts, bytecode, archives, runtime event streams, and suspicious non-placeholder secret assignments.
- Added v0.3.0 local plugin manifest validation, plugin permission registry, safe plugin context, registry, loader, lifecycle hooks, and failure-isolation tests.
- Added plugin developer documentation for manifests, permissions, lifecycle hooks, and safe local testing.
- Added v0.4.0 voice UX foundations: explicit voice state machine, safer wake-word matching, microphone diagnostics, push-to-talk fallback, TTS queue, and injected voice controller tests.
- Added voice setup and troubleshooting documentation for optional wake-word, push-to-talk, microphone, TTS, and offline STT behavior.

### Changed

- Split the monolithic product feature test suite into smaller domain-focused files for easier CI triage and maintenance.
- Updated README status and license information for GitHub publication.
- Cleaned repository ignore rules into plain English.
- Expanded environment template comments around free-first and optional integrations.
- Removed visible Settings, Plugins, Logs, and large wake-word control clutter from the main cockpit.
- Kept the assistant in wake-word standby with a minimal `STANDBY - SAY JARVIS` status.
- Hardened startup greeting voice output so TTS failures are logged without stopping the runtime.
- Kept arc reactor labels inside the canvas at smaller UI sizes.
- Updated the cockpit background to the blue-black `#0B0E1B` palette, reduced reactor label overlap, and modernized the window control cluster.
- Fine-tuned reactor label spacing, moved the title/subtitle block lower, and restyled the window controls into a flat dark strip with cyan controls.
- Removed the custom top-right window control strip, centered the date capsule independently, and refined vertical spacing around the reactor and title stack.
- Rebuilt the cockpit around the reference HUD layout with the requested palette, left icon rail, framed shell, terminal equalizer, top controls, and bottom status dock.
- Animated the terminal equalizer and bottom waveform so both HUD signal areas update continuously instead of using static drawings.
- Moved reusable HUD canvas drawing into `ui_hud_effects.py` to keep the main desktop window easier to maintain.
- Connected the reactor, status line, subtitle, title, equalizer activity, and runtime UI callbacks to the assistant state system.
- Normalized legacy runtime UI messages into professional terminal event categories.
- Split sidebar navigation and secondary page builders into focused UI modules.
- Replaced Phase 4 placeholder cards with live status/value/detail cards.
- Connected command routing, action execution, and TTS speech output to the cockpit state machine.
- Added a visual quality gate that captures Dashboard, System Monitor, Integrations, and Security pages.
- Updated CI dependency installation to include developer tooling required for linting and PyInstaller release builds.
- Hardened `.gitignore` for Python caches, env files, logs, archives, coverage output, IDE files, and generated release artifacts while keeping `.env.example` trackable.
- Treated release signing as optional for public source releases while keeping signing checks visible for executable and model artifact releases.
- Documented source release exclusions and pytest-compatible test execution.
- Reduced optional integration traceback noise for Groq, Spotify, microphone input, and TTS audio fallback paths.
- Improved plugin marketplace metadata with plugin IDs, permission summaries, risk levels, and manifest compatibility warnings.
- Preserved legacy plugin manifest compatibility while guiding new plugins toward stable `id` and explicit `permissions` fields.
- Hardened wake-word listener matching to use normalized whole-token detection and wake-word disabled mode.
- Expanded `.env.example` with optional voice, wake-word, push-to-talk, and TTS flags.

### Verified

- Product feature coverage now runs through focused startup/workflow, command/provider, security/memory, release/eval, audio/offline, and quality/maintenance test modules.
- Plugin coverage now includes manifest validation, permission boundaries, safe context behavior, registry discovery, loader isolation, lifecycle hooks, and security-boundary tests.
- Voice coverage now uses mocked microphone, wake-word, push-to-talk, TTS, and controller flows without requiring real audio hardware.
- Unit tests, Ruff linting, project audit, health check, and feature quality checks are used as the current quality gate.
