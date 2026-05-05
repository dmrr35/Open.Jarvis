# Feature Gap Roadmap

This document lists the current J.A.R.V.I.S feature inventory, the main gap for each feature, the recommended improvement, and the implementation difficulty. It is designed for open-source planning, issue creation, and release tracking.

## Current Feature Inventory

| Area | Feature | Current state | Gap or improvement needed | Difficulty | Priority |
|---|---|---|---|---|---|
| Voice runtime | Wake word detection | Available through the runtime wake listener. | Add configurable wake words and per-device sensitivity profiles. | Medium | High |
| Voice runtime | Command listening | Available through speech backend and command listener modules. | Add stronger retry behavior for noisy rooms and microphone disconnects. | Medium | High |
| Voice runtime | Active session timeout | Available through runtime timer logic. | Expose timeout tuning in the UI settings panel. | Easy | Medium |
| Voice runtime | Voice personality | British-style responses and personality helpers are available. | Add user-selectable tone presets and response length preferences. | Easy | Medium |
| Voice runtime | Text-to-speech | Edge TTS path is available. | Add automatic fallback when Edge TTS fails or the network is unstable. | Medium | High |
| Voice runtime | Offline speech profile | Offline profile support exists. | Add guided installers for Vosk, Piper, and local LLM providers. | Medium | High |
| Voice runtime | Voice calibration | Calibration recommendation logic exists. | Wire live microphone sampling into onboarding. | Medium | High |
| Command routing | Local intent router | Fast rule-based routing exists for common commands. | Add more examples, aliases, and per-command confidence traces. | Easy | High |
| Command routing | AI fallback router | Groq-based fallback exists. | Add provider health probes and better timeout reporting. | Medium | High |
| Command routing | LLM fallback strategy | Provider fallback structure exists. | Add local endpoint probing for Ollama or LM Studio. | Medium | High |
| Command routing | Action schema | Structured action validation exists. | Expand schema parameters per action so commands can be validated more strictly. | Medium | High |
| Command routing | Action dispatcher | Domain-based dispatcher exists. | Add richer execution metadata for UI logs and audits. | Easy | Medium |
| Runtime actions | Time and date | Available. | Add locale-aware formatting in settings. | Easy | Low |
| Runtime actions | CPU usage | Available. | Add threshold warnings and trend history. | Easy | Medium |
| Runtime actions | RAM usage | Available. | Add memory pressure recommendation text. | Easy | Medium |
| Runtime actions | Battery status | Available. | Add low-battery safety hints for long-running workflows. | Easy | Low |
| Runtime actions | Shutdown/restart/sleep | Available with safety confirmation. | Add clearer UI confirmation prompts and action audit records. | Medium | High |
| Runtime actions | Lock screen | Available with safety confirmation. | Keep confirmation and add configurable trusted-mode bypass. | Medium | Medium |
| Desktop control | Application launching | Browser, Chrome, Edge, Spotify, VS Code, calculator, and app aliases are supported. | Move app aliases to a user-editable config file. | Easy | High |
| Desktop control | Browser opening | Safe web opening exists. | Add browser preference selection in the UI. | Easy | Medium |
| Desktop control | Google search | Available through local routing and browser helpers. | Add safe-search and region preference settings. | Easy | Low |
| Desktop control | YouTube search | Available. | Add typed source metadata so UI can show the target site. | Easy | Low |
| Desktop control | Screenshot capture | Available. | Add save path setting and optional clipboard copy. | Easy | Medium |
| Desktop control | Clipboard reading | Available. | Add privacy masking before logging clipboard-derived summaries. | Medium | High |
| Desktop control | Clipboard summarization | Available through AI path. | Add local summarization fallback for offline mode. | Medium | Medium |
| Desktop control | Keyboard input | Available through safe desktop automation helpers. | Add per-command safety labels and UI confirmations. | Medium | High |
| Desktop control | Mouse input | Available through safe desktop automation helpers. | Add coordinate preview and dry-run mode. | Medium | Medium |
| Desktop control | Window management | Minimize, close, and related actions are supported. | Add active window title display before risky actions. | Medium | Medium |
| Memory | JSON memory store | Available. | Migrate to SQLite for durability, querying, and schema evolution. | Hard | High |
| Memory | Notes | Available. | Add edit, delete, restore, and tag support. | Medium | High |
| Memory | Preferences | Available. | Add conflict resolution when new preferences override old ones. | Medium | Medium |
| Memory | Habits | Available. | Add usage trend charts in the memory panel. | Medium | Medium |
| Memory | Short-term context | Available. | Persist resumable conversation summaries with privacy controls. | Hard | High |
| Memory | Memory insights | Available. | Add explainable insight sources so users know why a suggestion appeared. | Medium | Medium |
| Memory | Memory panel | Available. | Add bulk edit and restore operations. | Medium | Medium |
| Productivity | Command suggestions | Available. | Rank suggestions by recent failures, time of day, and user habits. | Medium | Medium |
| Productivity | Command history | Available and optimized for undo lookup. | Persist safe command history summaries between sessions. | Medium | Medium |
| Productivity | Undo support | Available through command history where actions support it. | Add UI-visible undo eligibility per action. | Easy | Medium |
| Productivity | Workflow mode | Basic workflow planning exists. | Add resumable workflow state persistence. | Hard | High |
| Productivity | Maintenance plan | Available. | Add dry-run estimates such as expected freed space. | Easy | Medium |
| Productivity | User profiles | Available. | Add profile switching from the UI and import/export support. | Medium | Medium |
| UI | Main desktop UI | Available in `arayuz.py`. | Continue migrating user-facing labels to reusable UI components. | Medium | High |
| UI | Service status display | Available. | Add provider connectivity status and last failure reason. | Medium | High |
| UI | Onboarding | Available. | Add live credential checks and microphone sampling. | Medium | High |
| UI | Settings dialogs | Available. | Add advanced settings search and validation warnings. | Medium | Medium |
| UI | Health center | Available with safe dry-run/apply repair wiring, masked runtime audit events, memory pruning, and log rotation. | Add setup validation repair coverage. | Medium | High |
| UI | Memory viewer | Available. | Add filtering, bulk actions, and restore. | Medium | Medium |
| UI | Runtime logs dialog | Available. | Add privacy masking and severity filters. | Medium | High |
| UI | Plugin marketplace UI | Available. | Wire approval buttons to signed enable or disable state changes. | Medium | High |
| UI | UI design system | Theme, rendering, and component helpers exist. | Add screenshot regression tests for the desktop UI. | Hard | Medium |
| Plugins | Plugin marketplace | Local marketplace logic exists. | Add remote signed catalog indexing. | Hard | High |
| Plugins | Plugin manifest security | Manifest validation exists. | Add richer permission descriptions and examples in docs. | Easy | Medium |
| Plugins | Plugin runner | Runner exists with sandbox-oriented checks. | Add deeper OS-level network isolation for third-party plugins. | Hard | High |
| Plugins | Plugin signatures | HMAC-style signature verification exists. | Move to asymmetric public-key signatures for public distribution. | Hard | High |
| Plugins | Plugin enable state | Enable state logic exists. | Add signed audit events and UI approval prompts. | Medium | High |
| Security | Runtime safety | Risk classification and confirmation logic exists. | Add per-profile safety rules for trusted and strict modes. | Medium | High |
| Security | URL safety | URL validation exists. | Add allowlist and blocklist editing in settings. | Medium | Medium |
| Security | Permission profiles | Available and visible in the cockpit panel. | Add per-profile safety rules for trusted and strict modes. | Medium | High |
| Security | Privacy mode | Runtime event details and structured context are masked before disk writes. | Extend masking policy to future external exporters. | Medium | High |
| Security | Process runner | Safe process execution helpers exist. | Add more explicit risky command explanations. | Easy | Medium |
| Observability | Runtime event logging | Available. | Add privacy masking and event sampling settings. | Medium | High |
| Observability | Latency snapshot | Available and recently optimized. | Add CI artifacts for startup, routing, and health-check timings. | Medium | Medium |
| Observability | SLO report | Available. | Add release baseline comparison. | Medium | Medium |
| Observability | Health checker | Available. | Add optional auto-fix suggestions with dry-run output. | Medium | High |
| Quality | Unit tests | Broad unit test suite exists. | Keep adding tests for each new feature and safety branch. | Easy | High |
| Quality | Eval suite | Available. | Add richer prompt fixtures and negative safety cases. | Medium | High |
| Quality | Eval runner | Available. | Connect measured evals to full voice pipeline fixtures. | Hard | Medium |
| Quality | Eval artifacts | Available. | Compare CI artifacts against previous release baselines automatically. | Medium | Medium |
| Quality | Project audit | Available. | Add more checks for public OSS readiness, license, and docs links. | Easy | High |
| Quality | E2E readiness | Available. | Add repeatable UI smoke paths for the desktop app. | Hard | Medium |
| Quality | Performance benchmarks | Available. | Run benchmarks in CI and publish summarized artifacts. | Medium | Medium |
| Release | Release build | Available. | Add installer notarization or signing notes and downloadable release notes. | Hard | Medium |
| Release | Release panel | Available. | Add CI artifact signature verification report. | Medium | Medium |
| Release | Release security config | Available. | Move public release catalogs to asymmetric signatures. | Hard | High |
| Release | Model installer | Available. | Add guided downloads with checksum verification before extraction. | Medium | High |
| Docs | README | Updated in English. | Add screenshots and badges after the repository is pushed. | Easy | High |
| Docs | Architecture docs | Available. | Add diagrams for command routing, plugin isolation, and memory flow. | Easy | Medium |
| Docs | Threat model | Available. | Add concrete abuse cases for plugins, clipboard, and browser automation. | Medium | High |
| Docs | Plugin security docs | Available. | Add developer checklist for third-party plugin submission. | Easy | Medium |
| Docs | Offline STT docs | Available. | Add tested install paths for Windows. | Easy | Medium |
| Docs | Contributing guide | Available. | Add branch naming, PR checklist, and test command matrix. | Easy | Medium |
| Docs | Security policy | Available. | Add supported versions after first tagged release. | Easy | Medium |
| Docs | Issue templates | Available. | Add performance bug and plugin review templates. | Easy | Low |
| Docs | CI workflow | Available. | Add artifact upload for evals, performance, and release manifest reports. | Medium | High |
| Repository | Git ignore | Available. | Confirm release artifacts and secrets stay out of public commits. | Easy | High |
| Repository | Environment template | Available. | Add comments explaining free API options and optional credentials. | Easy | High |
| Repository | Requirements | Available. | Consider splitting core, voice, UI, and dev requirements files. | Medium | Medium |

## Missing Features That Should Be Added

| Feature to add | Why it matters | Suggested implementation | Difficulty | Priority |
|---|---|---|---|---|
| Open-source license file | A public GitHub project needs explicit usage terms. | Add `LICENSE` with MIT, Apache-2.0, or another chosen license. | Easy | Critical |
| Changelog | Users need to understand version changes. | Add `CHANGELOG.md` using Keep a Changelog style. | Easy | High |
| GitHub badges | Improves OSS trust and quick status scanning. | Add CI, Python version, license, and tests badges to README after publishing. | Easy | Medium |
| README screenshots | Makes the assistant easier to evaluate quickly. | Add UI screenshots under `docs/assets/` and reference them in README. | Easy | High |
| Code of Conduct | Helpful for public collaboration. | Add `CODE_OF_CONDUCT.md`. | Easy | Medium |
| Pull request template | Keeps contributions consistent. | Add `.github/pull_request_template.md` with test and safety checklist. | Easy | High |
| Pre-commit config | Catches formatting and lint issues before CI. | Add `.pre-commit-config.yaml` for Ruff and basic file checks. | Medium | Medium |
| Requirements split | Keeps installs lighter for users who only need core features. | Add `requirements-core.txt`, `requirements-ui.txt`, and `requirements-dev.txt`. | Medium | Medium |
| English module aliases | Public API should be easier for global contributors. | Add English wrapper modules before renaming legacy Turkish files. | Medium | High |
| Safe file rename plan | Eventually remove Turkish legacy filenames without breaking imports. | Add compatibility shims, update imports, then deprecate old names. | Hard | Medium |
| Persistent tasks and reminders | A desktop assistant needs reliable productivity memory. | Add a local SQLite-backed task and reminder manager. | Medium | High |
| Local calendar integration | Enables real scheduling without paid services. | Add local calendar storage with import/export to `.ics`. | Medium | High |
| Email draft creation | Useful productivity feature without paid APIs. | Generate `mailto:` links or local `.eml` drafts. | Medium | Medium |
| Provider connectivity dashboard | Users need to know whether Groq, Gemini, and local providers work. | Add explicit check buttons with timeout and last error display. | Medium | High |
| Local LLM adapter | Keeps the project free and usable without cloud quotas. | Add Ollama and LM Studio adapters behind the same LLM interface. | Hard | High |
| SQLite memory migration | JSON memory will become fragile as the project grows. | Add migration from `memory.json` to `jarvis_memory.sqlite3`. | Hard | High |
| Semantic memory recall | Makes memory useful beyond exact keyword lookup. | Add local embeddings through sentence-transformers or a free local model. | Hard | High |
| OCR screen reading | Vision should help with desktop use even without paid APIs. | Add Tesseract OCR or EasyOCR fallback. | Hard | Medium |
| Local screen analysis | Reduces dependency on Gemini quota. | Add screenshot plus OCR plus UI element heuristics before cloud vision. | Hard | Medium |
| Developer agents | User requested coding/debugging/test agents in the target product vision. | Add bounded agents for review, test, and code generation with workspace safety rules. | Hard | High |
| Strong plugin isolation | Third-party plugins are the highest public OSS risk. | Use subprocess isolation, permission prompts, and optional network blocking. | Hard | Critical |
| Signed plugin catalog | Public marketplace features need tamper resistance. | Use asymmetric signatures for catalog and plugin packages. | Hard | Critical |
| UI screenshot regression tests | Prevents visual regressions in the desktop UI. | Add scripted UI render snapshots and compare stable components. | Hard | Medium |
| Performance CI artifacts | Keeps latency improvements from regressing. | Run `performance_benchmarks.py` in CI and upload report files. | Medium | Medium |
| Privacy-first logging policy | Clipboard, commands, and memory can contain sensitive data. | Mask sensitive fields before writing logs and document retention behavior. | Medium | Critical |
| Setup validation repair coverage | Makes onboarding state easier to diagnose without editing credentials. | Add allowlisted validation for setup state and environment template completeness. | Medium | High |
| Release packaging guide | Public users need a repeatable install path. | Document PyInstaller build, artifact checks, and release checklist. | Medium | Medium |
| Installer or portable build | Helps non-developer users try the assistant. | Produce a signed or clearly labeled unsigned Windows artifact. | Hard | Medium |

## Difficulty Groups

| Difficulty | Best first tasks | Expected outcome |
|---|---|---|
| Easy | License, changelog, README badges, screenshots, PR template, docs diagrams, issue template expansion, environment comments, project audit OSS checks. | The repository becomes easier to publish, understand, and contribute to. |
| Medium | Provider health dashboard, one-click health repairs, persistent command summaries, task/reminder storage, local calendar, email drafts, requirements split, UI approval wiring, privacy masking. | The assistant becomes more reliable and genuinely useful day to day. |
| Hard | SQLite memory migration, semantic recall, local LLM adapter, OCR/screen analysis, developer agents, plugin isolation, asymmetric signing, UI screenshot regression tests, release installer. | The project moves from strong prototype to serious modern AI assistant architecture. |

## Recommended Execution Plan

| Phase | Goal | Tasks | Acceptance criteria | Difficulty |
|---|---|---|---|---|
| 0 | Public repository readiness | Add license, changelog, PR template, README screenshots, badges, and OSS audit checks. | A new visitor can install, run, test, and understand project status from GitHub without private context. | Easy |
| 1 | Safety and observability hardening | Add provider probes, privacy-masked logs, active permission profile display, UI plugin approval wiring, and health dry-run fixes. | Risky actions are clearer, logs avoid sensitive leakage, and users can diagnose missing providers from the UI. | Medium |
| 2 | Productivity assistant core | Add persistent tasks, reminders, local calendar, `.ics` export/import, email draft creation, and command history persistence. | The assistant can manage daily productivity workflows fully locally and without paid APIs. | Medium |
| 3 | Memory and offline intelligence | Migrate memory to SQLite, add semantic recall, add local LLM provider adapters, and improve offline STT setup. | J.A.R.V.I.S works meaningfully even when cloud APIs are unavailable or rate-limited. | Hard |
| 4 | Vision and developer agents | Add OCR-first screen analysis, Gemini/local vision routing, bounded developer agents, and stronger plugin isolation. | The assistant can inspect the screen, help with code tasks, and safely run community extensions. | Hard |
| 5 | Release maturity | Add performance CI artifacts, UI snapshot checks, signed plugin/model catalogs, release packaging docs, and portable Windows build flow. | Each release has test evidence, latency evidence, signed metadata, and a repeatable install path. | Hard |

## Suggested Issue Order

| Order | Issue title | Difficulty | Depends on |
|---:|---|---|---|
| 1 | Add OSS license and changelog | Easy | None |
| 2 | Add PR template and README screenshots | Easy | None |
| 3 | Add OSS readiness checks to project audit | Easy | Issue 1 |
| 4 | Add provider connectivity probes | Medium | None |
| 5 | Mask sensitive runtime event details before disk writes | Medium | None |
| 6 | Surface active permission profile in the main UI | Easy | None |
| 7 | Persist safe command history summaries | Medium | None |
| 8 | Add local task and reminder manager | Medium | None |
| 9 | Add local calendar with `.ics` import/export | Medium | Issue 8 |
| 10 | Add email draft generation | Medium | None |
| 11 | Split requirements into core, UI, voice, and dev groups | Medium | None |
| 12 | Add SQLite memory migration | Hard | Issue 5 |
| 13 | Add semantic memory recall | Hard | Issue 12 |
| 14 | Add Ollama and LM Studio provider adapters | Hard | Issue 4 |
| 15 | Add OCR-first screen analysis | Hard | Issue 14 optional |
| 16 | Add developer review/test/code agents | Hard | Issue 5 |
| 17 | Move plugin signatures to asymmetric keys | Hard | Issue 5 |
| 18 | Add strong plugin isolation and approval audit | Hard | Issue 17 |
| 19 | Add performance CI artifacts | Medium | None |
| 20 | Add release packaging and portable Windows build guide | Hard | Issue 19 |

## Validation Commands

Run these after each implementation batch:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m ruff check .
python project_audit.py
python kontrol.py --no-pause
python feature_quality.py
```

For release-oriented changes, also run:

```powershell
python performance_benchmarks.py
python eval_runner.py
python release_build.py
```
