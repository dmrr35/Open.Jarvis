# J.A.R.V.I.S - Just A Rather Very Intelligent System

> "Sometimes you gotta run before you can walk." - Tony Stark

An AI desktop assistant inspired by Iron Man's JARVIS. Built with Python, powered by free-first local command routing with optional Groq cloud AI, and designed to combine voice control, desktop automation, memory, productivity helpers, plugin safety, release checks, and a cinematic cyber interface in one Windows-first system.

J.A.R.V.I.S can run in a keyless degraded mode. Local rules, the desktop UI, memory helpers, health checks, and many system commands work without API keys. Groq, Spotify, Gemini, and other cloud-backed capabilities are optional integrations.

---

## Features

- Wake word detection with `Jarvis`
- Natural language command handling with rule parsing plus Groq AI fallback
- Free-first local routing to reduce latency and API usage
- British-style voice responses with Edge TTS
- Custom cyber desktop UI with live service status
- Runtime states for `BOOTING`, `STANDBY`, `LISTENING`, `PROCESSING`, `EXECUTING`, `SPEAKING`, `ERROR`, and `OFFLINE`
- Command stream panel with structured terminal-style events
- Live system status bar with time, CPU, memory, latency, uptime, AI status, permission mode, and posture
- Memory system with notes, habits, preferences, short-term context, health scoring, and summaries
- Clipboard reading and Groq-backed or fallback summarization
- Browser opening, safe URL handling, Google search, and app launching
- Desktop automation for screenshots, keyboard shortcuts, mouse clicks, scrolling, and window control
- Spotify playback controls when Spotify credentials are configured
- Timers and runtime workflow helpers
- Privacy mode and secret masking before runtime events are written
- Permission profiles and destructive-action safety gates
- Plugin marketplace core, plugin trust state, signature verification, and sandboxed plugin execution helpers
- Offline STT planning with optional Vosk fallback support
- Health checker, project audit, repository hygiene checker, release readiness checker, eval suite, screenshot regression, and automated tests
- Release signing helpers, model catalog verification, and source-release hygiene tooling

---

## Planned Or Experimental Features

These items are documented roadmap work. They may have planning helpers or configuration placeholders, but they are not guaranteed production-ready flows yet.

- Gemini-backed vision analysis and screen understanding
- OCR with local fallback
- Semantic memory search with local embeddings
- Persistent tasks, reminders, and local calendar scheduling
- Email draft creation
- Research, summarization, and fact-check workflows
- Developer agents for coding, debugging, testing, and improvement reviews
- Rich local LLM adapter for Ollama or LM Studio
- Remote signed plugin catalogs
- Installer-grade Windows release packaging

---

## Project Structure

```text
Open.Jarvis/
+-- .github/                CI workflow and issue templates
+-- agents/                 Reserved for future agent implementations
+-- core/                   Reserved core package area
+-- docs/                   Architecture, threat model, plugin security, offline STT, and release docs
+-- evals/                  Evaluation support area
+-- open_jarvis/            Main source package
|   +-- app/                Package entry point for terminal mode
|   +-- audio/              ses_motoru.py, speech_backend.py, tts_provider.py, voice_calibration.py
|   +-- commands/           komutlar.py, local router, Groq router, action schema, dispatcher
|   |   `-- domains/        Runtime, media, and memory action handlers
|   +-- evaluation/         evaluation_suite.py, eval_runner.py, eval_artifacts.py, eval_measurements.py, performance_benchmarks.py
|   +-- health/             health_center.py, observability.py, feature_quality.py
|   +-- integrations/       llm_fallback.py, provider_health.py, offline_profile.py, model_installer.py, url_safety.py
|   +-- memory/             memory_*.py, privacy_mode.py, user_profiles.py, compatibility re-exports
|   +-- plugins/            permission_profiles.py, plugin_marketplace.py, plugin_runner.py, plugin_security.py, plugin_signature.py, plugin_state.py
|   +-- release/            repo_hygiene.py, project_audit.py, release_build.py, maintenance.py
|   +-- runtime/            jarvis_runtime.py, wake word, command listener, timer, orchestration, UI bridge, personality
|   +-- security/           jarvis_admin.py, release_security.py, public_release.py, security policy helpers
|   +-- ui/                 arayuz.py, ui_theme.py, ui_components.py, ui_*.py, memory_panel.py, security_center.py
|   `-- utils/              kontrol.py, jarvis_logging.py
+-- plugins/                Reserved for local plugin packages
+-- tests/                  Automated tests
+-- arayuz.py               Backward-compatible UI launcher
+-- jarvis.py               Backward-compatible terminal launcher
+-- kontrol.py              Backward-compatible health checker launcher
+-- repo_hygiene.py         Backward-compatible hygiene checker launcher
+-- project_audit.py        Backward-compatible static audit launcher
+-- public_release.py       Backward-compatible release readiness launcher
+-- eval_runner.py          Backward-compatible eval CLI launcher
+-- release_build.py        Backward-compatible release build launcher
+-- model_installer.py      Backward-compatible signed model catalog launcher
+-- .env.example            API key and runtime settings template
+-- .gitignore              Keeps secrets and generated files out of GitHub
+-- pyproject.toml          Ruff, mypy, and coverage configuration
+-- requirements.txt        Runtime dependencies
+-- requirements-dev.txt    Developer, lint, test, and build dependencies
+-- SECURITY.md             Security policy
+-- CONTRIBUTING.md         Contribution guide
+-- LICENSE                 MIT License
`-- README.md               This file
```

Generated runtime output such as `logs/`, `exports/`, `memory.json`, caches, build output, and release bundles should not be committed.

---

## Installation

Requirements:

- Windows 10 or 11
- Python 3.11+
- A working microphone for voice input
- Speakers or an audio output device for voice responses

Recommended install:

```powershell
python -m pip install -r requirements.txt
```

Developer install:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Manual package install:

```powershell
python -m pip install speechrecognition edge-tts pygame psutil requests groq spotipy pyautogui pyperclip customtkinter python-dotenv vosk schedule
python -m pip install pyaudio
```

If `pyaudio` fails on your machine, install it using a Windows wheel or your preferred package method.

Check installation:

```powershell
python kontrol.py --no-pause
```

---

## Setup

### 1. Groq API Key

- Go to [Groq Console](https://console.groq.com)
- Create an API key
- Copy your key

Groq is optional. Without it, J.A.R.V.I.S keeps local rule-based commands available and reports local-only mode.

### 2. Gemini API Key

- Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
- Create an API key
- Copy your key

Gemini is optional and currently reserved for future vision and multimodal workflows.

### 3. Spotify API Optional

- Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Create an app
- Add this redirect URI:

```text
http://127.0.0.1:8888/callback
```

- Copy your `Client ID` and `Client Secret`

Spotify is optional. Without it, Spotify commands return a clear disabled-mode message and the rest of the assistant continues.

### 4. Create Your `.env` File

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Then fill only the integrations you want:

```env
GROQ_API_KEY=
JARVIS_ENABLE_GROQ=false
JARVIS_GROQ_MODEL=llama-3.1-8b-instant
JARVIS_AI_MODE=auto
GEMINI_API_KEY=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=
JARVIS_ENABLE_SPOTIFY=false
```

Important:

- Never share your real `.env`
- Never push your real `.env` to GitHub
- Only commit `.env.example`
- Rotate any key that was ever exposed publicly

---

## Running

UI mode:

```powershell
python arayuz.py
```

Terminal mode:

```powershell
python -m open_jarvis.app.main
```

Backward-compatible terminal launcher:

```powershell
python jarvis.py
```

Weekly update script:

```powershell
python haftalik_guncelleme.py
```

Health checker:

```powershell
python kontrol.py --no-pause
```

Project audit:

```powershell
python project_audit.py
```

Repository hygiene check:

```powershell
python repo_hygiene.py --include-secrets
```

Public release readiness:

```powershell
python public_release.py
```

Public source safety scan:

```powershell
python scripts/public_release_check.py
```

Full test suite:

```powershell
python -m pytest
```

Unittest runner:

```powershell
python -m unittest discover -s tests -v
```

UI smoke test:

```powershell
python ui_smoke.py
```

UI screenshot regression:

```powershell
python ui_screenshot_regression.py
```

Lint:

```powershell
python -m ruff check .
```

---

## Voice Commands

### Activation

Say `Jarvis` to wake the assistant. After the command completes, it returns to standby mode.

### Applications

| Say | Action |
| --- | --- |
| `open browser` | Opens your preferred browser if mapped by the runtime |
| `open google chrome` | Opens Chrome |
| `open edge` | Opens Edge if mapped by the runtime |
| `open spotify` | Opens Spotify |
| `open vscode` | Opens VS Code |
| `open calculator` | Opens Calculator |
| `open notepad` | Opens Notepad |
| `open task manager` | Opens Task Manager |

### Web And Browser

| Say | Action |
| --- | --- |
| `open youtube` | Opens YouTube |
| `open github` | Opens GitHub |
| `open google` | Opens Google |
| `search for openai api` | Opens Google search results |
| `google python speech recognition` | Opens Google search results |
| `go to example.com` | Opens a normalized HTTPS URL |

### System Info

| Say | Action |
| --- | --- |
| `what time is it` | Reads the current time |
| `what day is it` | Reads the current date |
| `show ram usage` | Reads RAM usage |
| `show cpu usage` | Reads CPU usage |
| `show battery` | Reads battery status |

### Desktop Control

| Say | Action |
| --- | --- |
| `take a screenshot` | Saves a screenshot |
| `read clipboard` | Reads clipboard text |
| `summarize clipboard` | Summarizes copied text with Groq or local fallback |
| `minimize all` | Shows desktop |
| `maximize window` | Maximizes the active window |
| `close window` | Closes the active window |
| `volume up` | Raises volume |
| `volume down` | Lowers volume |
| `mute volume` | Toggles mute |
| `lock screen` | Requires permission before locking Windows |
| `shutdown` | Blocked unless destructive actions are explicitly allowed |

### Memory

| Say | Action |
| --- | --- |
| `favorite app is chrome` | Saves app preference when preference detection matches |
| `note buy milk` | Saves a note |
| `remember buy milk` | Saves a note |
| `read notes` | Reads saved notes |
| `my habits` | Reads most used commands |
| `memory stats` | Reads memory stats |
| `memory health` | Reads memory health |
| `memory summary` | Reads a memory summary |
| `daily summary` | Builds a daily assistant summary |
| `prune memory` | Runs safe memory cleanup |

### Spotify Optional

| Say | Action |
| --- | --- |
| `play music` | Starts playback when Spotify is configured |
| `pause music` | Pauses playback |
| `next track` | Skips to the next track |
| `previous track` | Returns to the previous track |
| `play lofi beats on spotify` | Searches and plays a track |
| `what is playing on spotify` | Reads current playback |

### Exit

| Say | Action |
| --- | --- |
| `goodbye jarvis` | Personal farewell and shutdown |
| `shut down jarvis` | Stops the assistant runtime |

---

## Safety

Dangerous actions are blocked unless explicitly allowed. This includes:

- shutdown
- restart
- sleep
- lock screen
- unsafe URLs
- risky plugin entrypoints
- destructive desktop actions
- risky input automation

Safety controls include:

- `JARVIS_ALLOW_DESTRUCTIVE_ACTIONS=false` by default
- `JARVIS_PERMISSION_PROFILE=normal` by default
- URL normalization that only allows HTTP and HTTPS browser links
- plugin path traversal checks
- plugin signature verification
- privacy mode for sensitive sessions
- secret masking before runtime event logs are written

Jarvis will use confirmation and permission controls where the action policy requires it.

---

## Keyless And Degraded Mode

J.A.R.V.I.S is designed to start without optional credentials.

| Missing item | Behavior |
| --- | --- |
| `.env` | Startup continues with defaults |
| `GROQ_API_KEY` | Groq cloud routing is disabled; local rule commands still work |
| `JARVIS_ENABLE_GROQ=false` | Groq cloud routing is disabled even if a key is present |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | Spotify actions are disabled with an actionable message |
| `JARVIS_ENABLE_SPOTIFY=false` | Spotify actions are disabled even if credentials are present |
| `GEMINI_API_KEY` | Future Gemini-backed flows stay unavailable |
| Microphone | UI and non-voice flows can still load; voice input reports an error state |
| Audio mixer | Voice output is disabled with a warning instead of crashing |

---

## Health And Quality

Current project quality checks include:

- automated health checker
- runtime service validation
- startup degraded-mode reporting for missing Groq, Spotify, microphone, and STT mode
- deterministic and measured eval coverage
- unit tests
- Ruff linting
- static project audit
- repository hygiene scanning
- public source secret and personal-data scanning
- public release readiness scanning
- memory and action history tracking
- release signing smoke checks
- signed model catalog verification
- feature quality reporting
- UI smoke and screenshot regression checks

Current verified baseline:

| Check | Current result |
| --- | --- |
| Unit tests | `228 passed` |
| Ruff | `All checks passed` |
| Project audit | `No static findings detected` |
| Repository hygiene | `PUBLIC RELEASE HYGIENE: PASS` after cleanup |
| Public source release check | `PUBLIC SOURCE RELEASE CHECK: PASS` |
| Public release readiness | `Ready: yes` |
| UI smoke | `UI smoke: ok` |
| UI screenshot regression | `dashboard`, `system`, `integrations`, and `security` passed |
| Health status | No critical blockers in keyless mode, with expected warnings |

Expected warnings in a fresh keyless setup:

- Groq API key not configured
- Spotify credentials missing
- optional release signing key missing
- microphone calibration not completed
- onboarding not completed

---

## Product Feature Inventory

| Feature | Status | Main files | Current gap or improvement |
| --- | --- | --- | --- |
| Wake word and runtime loop | Implemented | `jarvis_runtime.py`, `runtime/wake_word.py`, `runtime/wake_listener.py` | Add richer wake-word engines and live calibration UX |
| Speech recognition | Implemented | `speech_backend.py` | Improve offline quality with faster-whisper or guided Vosk profiles |
| Voice output | Implemented | `ses_motoru.py`, `tts_provider.py` | Add fully local Piper installer and voice preview UI |
| Startup degraded mode | Implemented | `runtime/readiness.py`, `jarvis_runtime.py` | Add UI repair buttons for each warning |
| Local command router | Implemented | `commands/local_intent_router.py` | Add fuzzy matching and more app/site aliases |
| Groq AI routing | Implemented optional | `commands/groq_router.py` | Add provider abstraction for local LLM endpoints |
| AI mode selection | Implemented | `llm_fallback.py` | Add live provider health probes with timeout |
| Action schema validation | Implemented | `commands/action_schema.py`, `commands/action_dispatcher.py` | Add per-action parameter schemas |
| Desktop automation | Implemented | `commands/domains/runtime_actions.py` | Add confirmation UX for risky input automation |
| Clipboard summarization | Implemented | `runtime_actions.py`, `groq_router.py` | Improve local summarizer quality |
| Memory notes and habits | Implemented | `memory.py`, `memory_*.py` | Move from JSON to SQLite and semantic search |
| Daily summary | Implemented | `commands/domains/memory_actions.py` | Include calendar/tasks after those modules exist |
| Spotify controls | Implemented optional | `commands/domains/media_actions.py` | Improve token refresh guidance and UI status |
| Timers | Implemented | `runtime/timer.py` | Add persisted reminders |
| UI cockpit | Implemented | `arayuz.py`, `ui_*.py` | Expand screenshot regression coverage as pages evolve |
| Health center | Implemented | `health_center.py`, `kontrol.py`, `ui_dialogs.py` | Add setup validation repair coverage |
| Runtime observability | Implemented | `observability.py`, `runtime/ui_bridge.py` | Add structured dashboards and log rotation |
| Live UI state bridge | Implemented | `runtime/ui_bridge.py`, `ui_state.py`, `komutlar.py`, `ses_motoru.py` | Add richer per-module state transitions |
| Plugin security | Implemented core | `plugin_security.py`, `plugin_signature.py`, `plugin_state.py`, `plugin_runner.py` | Add stronger OS-level isolation |
| Plugin marketplace UI | Implemented core | `plugin_marketplace.py`, `ui_plugin_marketplace.py` | Add remote signed catalog support |
| Eval suite | Implemented | `evaluation_suite.py`, `eval_runner.py`, `eval_measurements.py` | Add more real voice and safety fixtures |
| Release artifacts | Implemented | `release_build.py`, `release_security.py` | Add installer packaging and release notes |
| Offline profile | Implemented planning | `offline_profile.py`, `model_installer.py` | Add guided downloads and extraction |
| Vision analysis | Planned | future `vision/` package | Add screenshot OCR and Gemini/local fallback |
| Tasks and reminders | Planned | future `task_manager.py` | Add persistent task/reminder storage |
| Local calendar | Planned | future `calendar_manager.py` | Add local schedule model and command routing |
| Email drafts | Planned | future mail helper | Add safe draft-only creation |
| Developer agents | Planned | future `agents/` modules | Add explicit sandbox, tests, and approval flow |

---

## Product Feature Modules

These modules are intentionally small, testable, and reusable from the desktop app:

| Capability | Module | What it adds |
| --- | --- | --- |
| Onboarding checks | `onboarding_engine.py` | Groq, Spotify, Gemini, and microphone setup status |
| Permission profiles | `permission_profiles.py` | Safe, normal, and admin action policy matrix |
| Memory panel data | `memory_panel.py` | User-visible memory snapshot, preference update, and note deletion |
| Security overview | `security_center.py` | Permission profile, privacy mode, masked secret status, and confirmation-required action summary |
| Command history and undo | `command_history.py` | Recent command list with optional undo callbacks |
| Plugin marketplace | `plugin_marketplace.py` | Local plugin manifest scan, trust status, signature status, and enablement state |
| Local LLM fallback | `llm_fallback.py` | AI mode, provider selection, provider result shape, and offline/rules fallback |
| Workflow mode | `workflow_engine.py` | Multi-step task plans with rollback notes |
| Health center | `health_center.py` | Prioritized health cards, fix commands, safe dry-run/apply repairs, and repair audit events |
| Maintenance mode | `maintenance.py` | Safe memory, log, and cache cleanup recommendations |
| Repository hygiene | `repo_hygiene.py` | Detects local secrets, caches, logs, exports, build output, and executables before publishing |
| Public release readiness | `public_release.py` | Combines required docs, local hygiene, quality commands, and signing readiness into one release gate |
| Public source safety scan | `scripts/public_release_check.py` | Scans source-release files for secrets, tokens, private paths, private memory, logs, and cache artifacts |
| User profiles | `user_profiles.py` | Isolated settings and memory skeleton per user |
| Command suggestions | `command_suggestions.py` | Context-aware discoverability suggestions |
| TTS provider selection | `tts_provider.py` | Edge, Piper, and ElevenLabs provider metadata and environment selection |
| Plugin sandbox execution | `plugin_runner.py` | Trusted plugin execution in scoped temp workspaces with timeout and cleanup |
| Plugin signature verification | `plugin_signature.py` | Deterministic manifest signing and verification |
| Plugin enablement state | `plugin_state.py` | Enable/disable state, approval audit events, and `build_plugin_state_audit` |
| Offline profile | `offline_profile.py` | Local STT, TTS, and LLM readiness planning |
| Assistant eval suite | `evaluation_suite.py` | Intent, safety, latency, and STT release-gate scenarios |
| Eval measurements | `eval_measurements.py` | Command-router decisions, STT fixtures, and measured latency |
| Eval runner | `eval_runner.py` | Deterministic or measured release-gate execution |
| Eval artifact reports | `eval_artifacts.py` | JSON/Markdown release evidence and `compare_eval_artifacts` |
| Windows release artifact pipeline | `release_build.py` | PyInstaller build plan, SHA256 computation, signed manifest generation, and verification |
| Signed model catalog | `model_installer.py` | `build_signed_model_catalog`, `verify_model_catalog`, and `verify_model_checksum` |
| Voice calibration | `voice_calibration.py` | Microphone threshold recommendations from ambient samples |
| Performance benchmarks | `performance_benchmarks.py` | Budget comparison for startup, routing, and health checks |
| Release panel | `release_panel.py` | Signing readiness checks for CI and local release |
| Privacy mode | `privacy_mode.py` | Ephemeral session flags and secret masking |
| User-friendly errors | `error_messages.py` | Standard reason and next-step error messages |
| E2E readiness | `e2e_readiness.py` | Desktop-critical journey checklist for future automation |
| Feature quality registry | `feature_quality.py` | Core feature inventory with tests, performance budgets, and security notes |
| Cyber Hologram UI theme | `ui_theme.py` | Shared design tokens for the main window, dialogs, onboarding, and plugin views |
| UI components | `ui_components.py` | Reusable section, metric, info, status, and cockpit button components |
| UI smoke validation | `ui_smoke.py` | Builds the desktop shell without starting the assistant runtime thread |
| UI screenshot regression | `ui_screenshot_regression.py` | Captures key cockpit pages and verifies nonblank HUD visuals |

Feature quality CLI:

```powershell
python feature_quality.py
```

---

## Difficulty Roadmap

| Difficulty | Work item | Why it belongs here | Target files | Acceptance criteria |
| --- | --- | --- | --- | --- |
| Easy | Expand local English command phrases | Uses existing router and action payloads | `commands/local_intent_router.py` | More common commands bypass Groq and pass tests |
| Easy | Add README screenshots | Documentation-only | `README.md`, `docs/assets/` | GitHub page shows the UI clearly |
| Easy | Add command examples to tests | Pure test coverage | `tests/` | New examples pass without cloud calls |
| Easy | Add more health copy for optional integrations | Existing health model | `kontrol.py`, `health_center.py` | Warnings are clearer for new users |
| Medium | Add per-action parameter schemas | Shared validation design required | `commands/action_schema.py` | Invalid params are rejected before execution |
| Medium | Add provider health probes | Needs timeout/error handling | `llm_fallback.py`, `groq_router.py` | UI can show provider reachable/unreachable |
| Medium | Add persisted reminders | Requires storage and runtime wakeups | future `task_manager.py`, `runtime/` | Reminders survive restart |
| Medium | Add screenshot OCR | Needs dependency and fallback design | future `vision/`, `runtime_actions.py` | Text can be extracted locally from screenshots |
| Medium | Add setup validation repair coverage | Uses existing safe fix allowlist | `ui_dialogs.py`, `health_center.py`, `jarvis_admin.py` | Local setup state can be validated without editing credentials |
| Hard | SQLite memory migration | Data compatibility and migration risk | `memory_store.py`, `memory_*.py` | Existing JSON memory migrates safely |
| Hard | Semantic recall | Embeddings, privacy, ranking, and storage | future vector layer, `memory_*.py` | Memory search works offline with tests |
| Hard | Local LLM adapter | Endpoint differences and timeout behavior | `llm_fallback.py`, future providers | Ollama/LM Studio can route commands safely |
| Hard | Real vision assistant | Multimodal design and privacy concerns | future `vision/` package | Screen analysis works with local fallback |
| Hard | Developer agents | High safety and sandbox complexity | `agents/`, `plugin_runner.py` | Coding/debugging agents run with approvals and tests |
| Hard | Strong plugin isolation | OS-level process/network isolation required | `plugin_runner.py` | Third-party plugins have constrained execution |

---

## Current Next Roadmap

| Priority | Item | Difficulty | Status | Next step |
| --- | --- | --- | --- | --- |
| 1 | English OSS readiness pass | Easy | Complete | Keep scanning public docs and UI text before each release |
| 2 | License selection | Easy | Complete | `LICENSE` is present |
| 3 | README screenshots | Easy | Not started | Add UI screenshots under `docs/assets/` |
| 4 | Per-action schema validation | Medium | Partial | Add parameter schemas for each action |
| 5 | Provider health probes | Medium | Planned | Add timeout-based Groq/local endpoint checks |
| 6 | Persisted reminders | Medium | Planned | Add task/reminder storage module |
| 7 | SQLite memory migration | Hard | Planned | Design migration and rollback path |
| 8 | Local LLM adapter | Hard | Planned | Add provider interface and Ollama test double |
| 9 | OCR and screen analysis | Hard | Planned | Add local OCR package and screenshot pipeline |
| 10 | Developer agents | Hard | Planned | Design agent sandbox and approval model |

---

## Easy Roadmap Complete

| Item | Status | Evidence |
| --- | --- | --- |
| Security policy | Complete | `SECURITY.md` |
| Contribution guide | Complete | `CONTRIBUTING.md` |
| Issue templates | Complete | `.github/ISSUE_TEMPLATE/` |
| README comparison | Complete | `Compared With Other Jarvis Projects` |
| Health fix commands | Complete | Health reports include explicit fix commands |
| Feature quality dashboard | Complete | `python feature_quality.py` |
| Free-first local routing | Complete | `commands/local_intent_router.py` |
| Known limitations action plan | Complete | `Current Next Roadmap` |

---

## Compared With Other Jarvis Projects

Open.Jarvis is strongest in free-first desktop automation, local command routing, conservative safety gates, test coverage, health checks, release artifacts, and quality tracking. Larger assistant projects may be stronger in packaged distribution, cloud-scale integrations, community plugin ecosystems, and mature agent frameworks.

| Area | Open.Jarvis status | Gap before public maturity |
| --- | --- | --- |
| Safety | Destructive actions blocked by default, plugin signatures and sandbox helpers exist | Add stronger per-action confirmation UX |
| Quality | Unit tests, Ruff, audit, health check, eval artifacts, and screenshot regression exist | Add a larger eval set |
| Extensibility | Plugin trust, marketplace core, and plugin runner exist | Add remote signed plugin catalogs |
| Offline | Vosk fallback and offline profile planning exist | Add guided local STT/TTS/LLM installers |
| UX | Custom UI, onboarding, settings, runtime logs, health center, memory center | Add screenshots, guided calibration, and release installer |
| Agentic work | Workflow planning helpers exist | Add real developer agents with explicit sandbox and approvals |

---

## Settings Reference

| Setting | Purpose | Safe default |
| --- | --- | --- |
| `JARVIS_AI_MODE` | AI routing mode: `auto`, `free_cloud`, `offline`, or `rules` | `auto` |
| `JARVIS_ENABLE_GROQ` | Explicitly enable optional Groq cloud routing | `false` in `.env.example` |
| `JARVIS_GROQ_MODEL` | Groq model used for routing and summarization | `llama-3.1-8b-instant` |
| `JARVIS_WAKE_WORD` | Wake word used to activate the assistant | `jarvis` |
| `JARVIS_ACTIVE_TIMEOUT` | Seconds before returning to standby | `60` |
| `JARVIS_ACTION_SEQUENCE_DELAY` | Delay between multi-action workflow steps | `0.1` |
| `JARVIS_APP_LAUNCH_DELAY` | Short pause after launching apps | `0.2` |
| `JARVIS_CPU_SAMPLE_INTERVAL` | CPU usage sample duration for faster checks | `0.1` |
| `JARVIS_SCREENSHOT_DELAY` | Stabilization pause before screenshots | `0.2` |
| `JARVIS_SLEEP_ACTION_DELAY` | Delay before sending sleep command | `1.0` |
| `JARVIS_TYPE_DELAY` | Delay before automatic typing starts | `0.1` |
| `JARVIS_ENERGY_THRESHOLD` | Microphone sensitivity | `300` |
| `JARVIS_PAUSE_THRESHOLD` | Pause length for command segmentation | `1.0` |
| `JARVIS_TTS_PROVIDER` | Voice output provider selector | `edge` |
| `JARVIS_ALLOW_DESTRUCTIVE_ACTIONS` | Permit shutdown, restart, sleep, and lock actions | `false` |
| `JARVIS_PERMISSION_PROFILE` | Permission profile for runtime actions | `normal` |
| `JARVIS_PRIVACY_MODE` | Disable memory writes and tighten masking for sensitive sessions | `false` |
| `JARVIS_OFFLINE_STT` | Enable offline speech recognition fallback | `1` |
| `JARVIS_VOSK_MODEL_PATH` | Path to a local Vosk model | empty |
| `JARVIS_LOCAL_LLM_URL` | Optional local LLM endpoint | empty |
| `JARVIS_RELEASE_SIGNING_KEY` | HMAC signing key for release verification | empty |
| `JARVIS_PLUGIN_SIGNING_KEY` | HMAC signing key for local plugin signing | empty |
| `JARVIS_PLUGIN_SIGNING_KEYS` | Optional signer-to-key JSON for multiple plugin signers | empty |
| `GROQ_API_KEY` | Optional AI command routing and summarization key | empty |
| `JARVIS_ENABLE_SPOTIFY` | Explicitly enable optional Spotify controls | `false` in `.env.example` |
| `SPOTIFY_CLIENT_ID` | Optional Spotify API client ID | empty |
| `SPOTIFY_CLIENT_SECRET` | Optional Spotify API client secret | empty |
| `SPOTIFY_REDIRECT_URI` | Spotify callback URI | `http://127.0.0.1:8888/callback` |
| `GEMINI_API_KEY` | Optional future Gemini integration | empty |

---

## Notes

- J.A.R.V.I.S works without Spotify credentials; only Spotify features stay unavailable.
- J.A.R.V.I.S works without Groq credentials for local-rule commands.
- Gemini is optional and currently reserved for future vision workflows.
- Desktop automation is Windows-first.
- Voice quality depends on microphone hardware and room noise.
- Logs are written to `logs/jarvis.log`.
- Runtime events are written to `logs/runtime_events.jsonl`.
- Offline STT details live in `docs/OFFLINE_STT.md`.
- Plugin security details live in `docs/PLUGIN_SECURITY.md`.
- Release signing details live in `docs/RELEASE_SIGNING.md`.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
