# Offline Speech Recognition

JARVIS can fall back to offline transcription when a local Vosk model is available.

## Enable

- Set `JARVIS_OFFLINE_STT=1`
- Point `JARVIS_VOSK_MODEL_PATH` to a local Vosk model directory

## Behavior

- JARVIS tries online Google speech recognition first
- If that fails, it checks for a local Vosk model
- If no model is available, it returns a helpful degraded-mode message

## Model locations

Common candidates:

- `%USERPROFILE%\.open_jarvis\vosk_models`
- `models/vosk-model-small-en-us-0.15`
- `model`

## Signed model catalog

Release builds publish a signed model catalog with expected checksums for supported offline profiles:

- Vosk STT profile
- Piper TTS profile
- Ollama local LLM profile

Generate a local catalog:

```bash
python model_installer.py --write-catalog release/model-catalog-local.json
```

`model_installer.verify_model_catalog(...)` verifies the catalog signature before install plans use catalog checksums. `model_installer.verify_model_checksum(...)` verifies downloaded archives before extraction or configuration.
