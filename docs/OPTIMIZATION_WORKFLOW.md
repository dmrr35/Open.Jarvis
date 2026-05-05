# J.A.R.V.I.S Optimization Workflow

This workflow keeps optimization measurable, free-first, and safe for an open-source desktop assistant.

## Current Scan Baseline

| Area | Current result | Action |
|---|---:|---|
| Python source files | 107 | Keep module boundaries small and test-covered. |
| Unit tests | 199 passing | Keep this as the minimum local gate before publishing. |
| Static audit | 0 findings | Keep `python project_audit.py` clean before release. |
| Ruff | Passing | Run after each code change. |
| Dependency health | No broken requirements | Re-run after dependency updates. |
| Health check | No critical blockers | Review runtime, onboarding, microphone, Spotify, and memory warnings. |
| Feature quality | 27/27 production-ready core, 94.4 average | Prioritize the listed next improvements by user impact. |
| Performance budget smoke | 5/5 budget examples passing | Replace example timings with measured CI timings. |

## Phase 1 - Measure Before Changing

| Target | Metric | Command | Pass target |
|---|---|---|---|
| Full behavior | Unit tests | `python -m unittest discover -s tests -p "test_*.py"` | 0 failures |
| Code quality | Ruff | `python -m ruff check .` | 0 findings |
| Maintainability | Static audit | `python project_audit.py` | 0 findings |
| Runtime readiness | Health check | `python kontrol.py --no-pause` | No critical blockers |
| Dependency graph | Pip check | `python -m pip check` | No broken requirements |

## Phase 2 - Voice Latency

| Work item | Difficulty | Why it matters | Done when |
|---|---|---|---|
| Make wake listener independent from greeting playback | Easy | Startup TTS should never block wake-word readiness. | Wake listener starts even if TTS fails. |
| Add timed spans around wake detection, STT, routing, and TTS | Medium | Latency must be visible per stage. | Runtime logs include stage timings. |
| Cache common TTS phrases locally | Medium | Greeting and fixed responses should play faster. | Repeated fixed phrases avoid fresh network TTS calls. |
| Add offline Piper TTS option | Hard | Removes cloud delay and internet dependency. | `JARVIS_TTS_PROVIDER=piper` works with tests and docs. |

## Phase 3 - Command Routing

| Work item | Difficulty | Why it matters | Done when |
|---|---|---|---|
| Expand local intent coverage for common commands | Easy | More commands bypass Groq and feel instant. | New local phrases pass router tests. |
| Add per-action parameter schemas | Medium | Bad AI payloads should be rejected early. | Invalid payloads fail before execution. |
| Add AI timeout and retry budget per provider | Medium | Cloud calls should not freeze the assistant. | Groq/Gemini fallback uses bounded timeouts. |
| Add measured eval artifacts to CI comparison | Hard | Releases should not regress command quality. | CI compares current eval metrics against previous artifacts. |

## Phase 4 - UI Runtime Performance

| Work item | Difficulty | Why it matters | Done when |
|---|---|---|---|
| Keep cockpit controls minimal | Easy | The assistant should feel like a system, not a settings panel. | Only telemetry and assistant state are visible by default. |
| Add screenshot regression tests | Medium | Hologram layout should not break visually. | CI captures and compares UI screenshots. |
| Add frame budget tracking for canvas animation | Medium | The arc reactor should stay smooth on weaker machines. | Slow frames are logged as runtime warnings. |
| Move heavy dialogs into lazy-loaded modules | Hard | Startup should stay fast as tools grow. | UI startup time stays under budget with optional dialogs. |

## Phase 5 - Memory And Logs

| Work item | Difficulty | Why it matters | Done when |
|---|---|---|---|
| Prune stale memory during maintenance | Easy | Smaller memory improves recall speed and health score. | Health warning drops after safe pruning. |
| Rotate noisy runtime logs automatically | Easy | Health posture should reflect current state, not old noise. | Log rotation is available from safe repair flow. |
| Add indexed memory search metrics | Medium | Semantic recall needs predictable speed. | Memory queries report duration and hit count. |
| Add encrypted private memory export/import | Hard | Public OSS users need safe backup without leaking secrets. | Exports are encrypted and covered by tests. |

## Phase 6 - Release Gate

Before publishing a release, run this exact gate:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m ruff check .
python project_audit.py
python kontrol.py --no-pause
python feature_quality.py
python -m pip check
```

Release only when tests, lint, static audit, feature quality, and dependency checks pass. Health warnings are acceptable only when they are optional integration warnings documented in the README.
