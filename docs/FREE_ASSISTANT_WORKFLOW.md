# Free-First Assistant Workflow

This document describes the architecture path for keeping Open.Jarvis free-first, assistant-focused, modular, and suitable for public open-source release.

## Core Decision

Open.Jarvis should remain a personal desktop assistant before it becomes a broader automation platform. Home automation, paid integrations, and broad autonomous browsing are intentionally out of scope for the first public roadmap.

Priority order:

1. Understand common voice commands quickly and reliably.
2. Run simple commands locally without sending them to an LLM.
3. Use free-tier cloud AI only when natural-language reasoning is actually needed.
4. Keep the assistant usable when API keys are missing or free quotas are exhausted.
5. Grow memory, productivity, screen analysis, and developer-assistant features in small, testable modules.

## Current Architecture Snapshot

The project already has a solid modular base:

- `jarvis_runtime.py`: main runtime loop, wake-word activation, and command listening.
- `speech_backend.py`: online speech recognition with optional Vosk offline fallback.
- `commands/local_intent_router.py`: free local routing for common commands.
- `commands/groq_router.py`: Groq-backed command analysis and JSON action generation.
- `commands/action_schema.py`: shared action-payload validation.
- `commands/action_dispatcher.py`: routes action payloads to domain handlers.
- `commands/domains/runtime_actions.py`: desktop, system, browser, clipboard, and screenshot actions.
- `commands/domains/media_actions.py`: Spotify actions.
- `commands/domains/memory_actions.py`: notes, memory stats, memory health, and daily summary actions.
- `memory*.py`: notes, habits, preferences, short-term context, and memory insight helpers.
- `llm_fallback.py`: AI mode and provider selection.
- `observability.py`: structured runtime events and latency metrics.

Main risk:

- Routing every command through cloud AI increases latency and consumes free-tier quota.

Main opportunity:

- The action dispatcher is already strong. The local intent router lets common commands run faster, cheaper, and offline.

## Free-First Tech Stack

### Command Understanding

Recommended provider order:

1. Local rules.
2. Groq free-tier API.
3. Optional local LLM endpoint such as Ollama or LM Studio.
4. Optional free-model provider.
5. Safe fallback response.

Recommended libraries and APIs:

- `groq`: optional cloud routing and summarization.
- `llm_fallback.py`: provider selection and AI mode policy.
- `commands/local_intent_router.py`: deterministic local routing.
- `commands/action_schema.py`: action payload validation.
- `pydantic`: future per-action schema validation if stronger typing is needed.
- `rapidfuzz`: future fuzzy matching for local command phrases.

### Speech

Current:

- `speechrecognition`
- `vosk`
- `edge-tts`

Recommended next additions:

- `faster-whisper`: higher-quality local STT option.
- WebRTC VAD or Silero VAD: faster speech-start and speech-end detection.
- Piper: fully local TTS option.

### Desktop Assistant

Current:

- `pyautogui`
- `pyperclip`
- `psutil`
- `webbrowser`

Recommended next additions:

- `pywinauto`: more stable Windows application automation.
- `mss`: faster screenshots.
- `sqlite3`: durable local storage for memory and tasks.

### Memory

Current:

- JSON-backed notes, preferences, habits, and short-term context.

Medium target:

- SQLite tables for `notes`, `preferences`, `habits`, `sessions`, and `command_history`.

Hard target:

- Local embedding search with ChromaDB, sqlite-vec, or a small sentence-transformers model.

### Vision

Assistant-focused vision should prioritize:

- Screenshot OCR.
- Screen-error explanation.
- Window/application state summaries.
- Optional Gemini vision analysis only when the user configures an API key.

Recommended libraries:

- `opencv-python`
- `pytesseract` or `easyocr`
- `mss`

## Runtime Flow

```text
Wake word
  -> Audio capture
  -> STT
  -> Command normalizer
  -> Local intent router
       -> Match found: validate action and execute locally
       -> No match: send to configured AI provider
             -> Valid JSON action: validate schema
             -> Invalid/error/rate-limit: fallback router or safe talk response
  -> Action dispatcher
  -> Domain handler
  -> TTS response
  -> Runtime event and latency metrics
```

This flow keeps commands such as `what time is it`, `open chrome`, `memory stats`, `take screenshot`, and `add note ...` fast and free.

## Difficulty Classification

### Easy

| Work item | Why it is easy | Main files | Estimate |
| --- | --- | --- | --- |
| Expand local intent phrases | Uses existing action payloads | `commands/local_intent_router.py` | 0.5-1 day |
| Add more local command tests | Test-only coverage | `tests/test_local_intent_router.py` | 0.5 day |
| Improve optional integration messages | Existing health model | `kontrol.py`, `health_center.py` | 0.5-1 day |
| Add README screenshots | Documentation-only | `README.md`, `docs/assets/` | 0.5 day |
| Add GitHub badges | Documentation-only | `README.md` | 0.5 day |

### Medium

| Work item | Why it is medium | Main files | Estimate |
| --- | --- | --- | --- |
| Per-action parameter schemas | Shared validation needs action-specific rules | `commands/action_schema.py` | 1-2 days |
| Provider health probes | Needs timeout, error handling, and UI status | `llm_fallback.py`, `groq_router.py`, `arayuz.py` | 2-3 days |
| Persisted reminders | Needs storage and runtime scheduling | future `task_manager.py`, `runtime/` | 2-4 days |
| Local OCR workflow | New dependency and screenshot pipeline | future `vision/`, `runtime_actions.py` | 3-5 days |
| One-click health fixes | UI plus safety review | `ui_dialogs.py`, `health_center.py` | 2-4 days |

### Hard

| Work item | Why it is hard | Main files | Estimate |
| --- | --- | --- | --- |
| SQLite memory migration | Data migration and rollback risk | `memory_store.py`, `memory_*.py` | 4-7 days |
| Semantic recall | Embeddings, ranking, privacy, and storage | future vector layer | 5-10 days |
| Local LLM adapter | Endpoint differences and timeout behavior | `llm_fallback.py`, future provider modules | 4-7 days |
| Real vision assistant | Multimodal design and privacy considerations | future `vision/` | 5-10 days |
| Developer agents | High safety and sandbox complexity | future `agents/` modules | 7-14 days |
| Strong plugin isolation | OS-level process and network isolation | `plugin_runner.py` | 7-14 days |

## Recommended Implementation Order

| Order | Item | Difficulty | Reason |
| --- | --- | --- | --- |
| 1 | Finish English OSS readiness | Easy | Public trust and contributor clarity |
| 2 | Add license and screenshots | Easy | Required before public launch |
| 3 | Expand local English commands | Easy | Immediate speed and free-tier benefit |
| 4 | Add per-action schemas | Medium | Protects every provider path |
| 5 | Add provider health probes | Medium | Makes AI mode visible and debuggable |
| 6 | Add persisted reminders | Medium | High user value without heavy AI risk |
| 7 | Add SQLite memory migration | Hard | Foundation for durable memory |
| 8 | Add local LLM provider | Hard | Enables stronger offline mode |
| 9 | Add OCR/screen analysis | Hard | Opens the vision roadmap safely |
| 10 | Add developer agents | Hard | Needs strong sandbox and approvals |

## Error Handling Policy

Every AI provider should eventually return a stable result envelope:

```python
ProviderResult(
    ok=True,
    provider="groq",
    mode="free_cloud",
    action={...},
    error=None,
    latency_ms=320,
)
```

Recommended error categories:

- `RateLimitError`: free quota or rate limit reached; activate cooldown.
- `ProviderUnavailableError`: API or local endpoint unavailable; fall back to rules.
- `InvalidActionError`: model returned invalid JSON or invalid action payload.
- `UnsafeActionError`: action requires confirmation or is blocked.
- `SpeechTimeoutError`: no speech detected; return to standby.

## Latency Optimization

Main latency sources:

- STT wait time.
- Cloud AI round trip.
- TTS startup.
- Desktop automation stabilization delays.

Recommended improvements:

- Keep common commands on the local router.
- Add VAD to detect speech boundaries sooner.
- Keep TTS responses short by default.
- Track `local_router`, `llm_router`, and `action_dispatch` latency metrics.
- Use a fast free-tier Groq model for routing.
- Avoid unnecessary sleeps in PyAutoGUI flows.

## Free-Service Policy

Rules:

- No card-required service should be mandatory.
- Free-tier quota exhaustion must not break local commands.
- Paid-provider features must be optional and disabled by default.
- Users without API keys must still be able to use the core assistant.
- Every cloud provider should remain an adapter, not a hard dependency.

| Need | Default | Fallback | Notes |
| --- | --- | --- | --- |
| Simple commands | Local rules | None | Fastest and free |
| NLP routing | Groq free-tier | Local LLM or rules | Watch free-tier limits |
| STT | SpeechRecognition or Vosk | faster-whisper later | Online STT has privacy and availability tradeoffs |
| TTS | Edge TTS | Piper later | Edge TTS is the current default |
| Memory | JSON now, SQLite later | None | Local and free |
| OCR | Local OCR later | Gemini optional | Avoid mandatory vision APIs |
| Summarization | Groq when configured | Local extractive summary | Free-tier safe |

## Acceptance Criteria

The architecture is on track when:

- Basic commands work without a Groq API key.
- Groq is used only when local routing cannot handle the command.
- Rate limits trigger cooldown instead of repeated failing requests.
- Local command latency remains visibly lower than cloud routing.
- The assistant remains desktop-assistant focused.
- New features can be added as domain handlers.
- UI and logs expose active AI mode, provider, and latency metrics.
