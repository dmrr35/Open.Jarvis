"""
VOICE ENGINE - Microsoft Edge TTS
Manages JARVIS speech output.
"""

import asyncio
import io

import edge_tts
import pygame
from edge_tts.exceptions import EdgeTTSException

from open_jarvis.runtime.ui_bridge import send_log, send_state

try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    MIXER_READY = True
except pygame.error as exc:
    MIXER_READY = False
    send_log(f"[WARN] TTS audio mixer unavailable. Voice output disabled: {exc}")

VOICE = "en-GB-RyanNeural"  # Closest to Iron Man JARVIS voice
RATE = "-8%"
PITCH = "-12Hz"


async def _speak_async(text: str):
    if not MIXER_READY:
        return
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    if not audio_data:
        return
    audio_io = io.BytesIO(audio_data)
    pygame.mixer.music.load(audio_io, "mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)


def speak(text: str):
    send_state("SPEAKING", "Voice response active")
    send_log(f"[SPEAKING] Speaking started: {text[:120]}")
    print(f"JARVIS: {text}")
    try:
        asyncio.run(_speak_async(text))
    except (EdgeTTSException, OSError, RuntimeError, pygame.error) as exc:
        send_log(f"[WARN] Voice output failed: {exc}")
    finally:
        send_log("[OK] Speaking completed")


# Keep Turkish alias for backward compatibility
if __name__ == "__main__":
    speak("All systems online. Jarvis is ready, sir.")
