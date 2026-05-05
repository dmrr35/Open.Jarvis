# Architecture

Open.Jarvis is a desktop AI assistant with a deliberately layered design.

## Data Flow

1. Voice or UI input enters through `jarvis.py`, `jarvis_runtime.py`, or `arayuz.py`.
2. Runtime orchestration routes commands through `runtime/` and `commands/`.
3. Domain handlers execute desktop, media, memory, plugin, and system actions.
4. Safety gates validate destructive actions, URL handling, plugin trust, and privacy mode.
5. Observability records runtime events into `logs/runtime_events.jsonl`.
6. Health, onboarding, release, eval, and feature-quality modules expose testable pure helpers.

## Main Layers

| Layer | Modules | Responsibility |
|---|---|---|
| UI | `arayuz.py`, `ui_*.py` | Desktop experience and user-facing dialogs |
| Runtime | `jarvis_runtime.py`, `runtime/` | Listening, orchestration, lifecycle |
| Commands | `commands/` | Desktop, media, memory, and routed actions |
| Safety | `runtime_safety.py`, `url_safety.py`, `plugin_security.py` | Policy enforcement |
| Product core | `*_panel.py`, `*_profile.py`, `*_runner.py` | Reusable, testable feature logic |
| Operations | `kontrol.py`, `project_audit.py`, `feature_quality.py` | Quality and health gates |

## Design Rules

- Keep user-visible behavior in small, testable helper modules.
- Keep desktop side effects behind domain handlers and process helpers.
- Keep secrets in `.env`, never in source or generated reports.
- Keep plugin execution behind trust validation and sandbox planning.
