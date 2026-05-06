# Voice Troubleshooting

## The App Starts But Voice Is Unavailable

This is an expected degraded mode. Check:

- `JARVIS_VOICE_ENABLED=true`
- microphone access is allowed in Windows privacy settings
- your microphone appears in Windows sound input devices
- `pyaudio` and `speechrecognition` are installed

The UI and text commands should remain usable even when voice input is disabled.

## Wake Word Does Not Trigger

Check:

- `JARVIS_WAKE_WORD_ENABLED=true`
- `JARVIS_WAKE_WORD=jarvis` or your preferred phrase
- `JARVIS_ENERGY_THRESHOLD` is not too high
- room noise is not overwhelming the microphone

If wake-word mode is unreliable, disable it and use push-to-talk or text commands.

## Wake Word Triggers Too Often

Increase `JARVIS_WAKE_WORD_COOLDOWN_SECONDS` slightly or rerun microphone calibration and use the recommended `JARVIS_ENERGY_THRESHOLD`.

## TTS Does Not Speak

Check:

- `JARVIS_TTS_ENABLED=true`
- `JARVIS_TTS_PROVIDER=edge`
- an audio output device is available
- pygame mixer initialization is not blocked by the local audio driver

TTS failure should be isolated. Commands should still complete even when speech output is unavailable.

## Offline STT

Set `JARVIS_OFFLINE_STT=1` and configure `JARVIS_VOSK_MODEL_PATH` only after downloading a Vosk model. If no model is configured, Open.Jarvis should continue in reduced mode rather than requiring the model at startup.

## CI And Tests

CI does not use real audio hardware. Voice tests rely on mocked probes, fake listeners, and fake playback callbacks.
