"""Media and Spotify actions."""

from __future__ import annotations

import os

import spotipy
from dotenv import load_dotenv
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from jarvis_admin import format_actionable_message

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"

sp = None


def _env_flag_enabled(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def spotify_enabled() -> bool:
    """Return whether optional Spotify controls are enabled by configuration."""

    return _env_flag_enabled("JARVIS_ENABLE_SPOTIFY", default=True)


def get_spotify_client():
    """Create the Spotify client only when a Spotify action is requested."""

    global sp
    if sp is not None:
        return sp
    if not spotify_enabled():
        return None
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        return None
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
            )
        )
    except (OSError, SpotifyException):
        sp = None
    return sp


def clamp_volume(level, default: int = 50) -> int:
    """Return a Spotify-safe volume percentage."""

    try:
        value = int(level)
    except (TypeError, ValueError):
        value = default
    return max(0, min(100, value))


def handle_media_action(action: str, params: dict, context: dict) -> bool | None:
    """Handle Spotify playback actions."""

    if not action.startswith("spotify_"):
        return None

    speak = context["speak"]
    logger = context["logger"]

    spotify_client = get_spotify_client()
    if spotify_client is None:
        speak(
            format_actionable_message(
                "Spotify credentials not found. Spotify integration disabled.",
                "The Spotify integration is disabled or the client credentials are missing.",
                "Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to .env, then set JARVIS_ENABLE_SPOTIFY=true.",
            )
        )
        return True

    try:
        if action == "spotify_play":
            spotify_client.start_playback()
        elif action == "spotify_pause":
            spotify_client.pause_playback()
        elif action == "spotify_next":
            spotify_client.next_track()
        elif action == "spotify_prev":
            spotify_client.previous_track()
        elif action == "spotify_volume":
            spotify_client.volume(clamp_volume(params.get("level", 50)))
        elif action == "spotify_search":
            query = params.get("query", "")
            results = spotify_client.search(q=query, limit=1, type="track")
            tracks = results["tracks"]["items"]
            if tracks:
                spotify_client.start_playback(uris=[tracks[0]["uri"]])
                speak(f"Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}, sir.")
            else:
                speak(f"Couldn't find {query}, sir.")
        elif action == "spotify_current":
            current = spotify_client.current_playback()
            if current and current["is_playing"]:
                speak(f"Currently playing {current['item']['name']} by {current['item']['artists'][0]['name']}, sir.")
            else:
                speak("Nothing is playing, sir.")
        else:
            logger.warning("Unhandled Spotify action: %s", action)
            return None
        return True
    except (OSError, RuntimeError, SpotifyException) as exc:
        logger.warning("Spotify action failed: %s", exc)
        speak(
            format_actionable_message(
                f"I couldn't complete {action.replace('_', ' ')}, sir.",
                "Spotify may be closed, or the access token may have expired.",
                "Open Spotify, re-authorize if needed, and try again.",
            )
        )
        return True
