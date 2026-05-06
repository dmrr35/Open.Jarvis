# Voice Setup

Open.Jarvis treats voice as optional. The desktop UI, text commands, local routing, memory helpers, health checks, and release tooling should still work when no microphone, speaker, Groq key, Spotify credentials, or Vosk model is available.

## Configuration

Copy `.env.example` to `.env`, then tune only the values you need:

```env
JARVIS_VOICE_ENABLED=true
JARVIS_WAKE_WORD=jarvis
JARVIS_WAKE_WORD_ENABLED=true
JARVIS_WAKE_WORD_COOLDOWN_SECONDS=1.0
JARVIS_PUSH_TO_TALK_ENABLED=true
JARVIS_TTS_ENABLED=true
JARVIS_TTS_PROVIDER=edge
JARVIS_OFFLINE_STT=1
JARVIS_VOSK_MODEL_PATH=
```

Set `JARVIS_WAKE_WORD_ENABLED=false` to avoid always-listening wake-word behavior and use text commands or push-to-talk flows instead. Set `JARVIS_TTS_ENABLED=false` if your machine has no reliable audio output.

## Wake Word

The wake-word matcher normalizes case, whitespace, and punctuation. It avoids unsafe substring matches, so `jarvis` can match `Hey, Jarvis!` but should not match unrelated words that merely contain those letters.

## Push-To-Talk

Push-to-talk bypasses wake-word detection but still checks microphone availability. If no microphone is available, it returns a degraded-mode warning instead of crashing the app.

## Microphone Calibration

The calibration helper uses ambient sample values to recommend `JARVIS_ENERGY_THRESHOLD`. Start with the default `300`, then adjust only if wake-word or command detection is too sensitive or not sensitive enough.

## TTS

The TTS queue serializes speech requests so responses do not overlap. Playback failures are isolated and reported as warnings; they should not stop command processing.

## Tests

Voice tests use fakes and injected probes. They do not require a real microphone, speaker, Vosk model, Groq key, Spotify credentials, or network access.
