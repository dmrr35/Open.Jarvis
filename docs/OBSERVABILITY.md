# Runtime Observability

JARVIS now writes structured runtime events to `logs/runtime_events.jsonl`.

## Event types

- `startup`
- `wake_word`
- `command_recognized`
- `command_executed`
- `voice_error`
- `groq_request`
- `groq_error`
- `app_launch`

## Health signals

The health checker now includes:

- memory score
- runtime posture
- warning and error counts from recent events
