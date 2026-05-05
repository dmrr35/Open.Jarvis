import unittest
from unittest.mock import patch

import open_jarvis.commands.domains.media_actions as media_actions
from open_jarvis.commands.domains.media_actions import clamp_volume, get_spotify_client


class DummyLogger:
    def __init__(self):
        self.messages = []

    def warning(self, message, *args):
        self.messages.append(("warning", message % args if args else message))

    def exception(self, message, *args):
        self.messages.append(("exception", message % args if args else message))


class MediaActionsTests(unittest.TestCase):
    def test_clamp_volume_keeps_spotify_range_safe(self):
        self.assertEqual(clamp_volume(-10), 0)
        self.assertEqual(clamp_volume(50), 50)
        self.assertEqual(clamp_volume(999), 100)
        self.assertEqual(clamp_volume("bad"), 50)

    def test_spotify_client_is_created_lazily_and_cached(self):
        original_sp = media_actions.sp
        media_actions.sp = None
        try:
            with (
                patch.object(media_actions, "SPOTIFY_CLIENT_ID", "id"),
                patch.object(media_actions, "SPOTIFY_CLIENT_SECRET", "secret"),
                patch.object(media_actions, "SpotifyOAuth") as oauth_mock,
                patch.object(media_actions.spotipy, "Spotify") as spotify_mock,
            ):
                spotify_mock.return_value = object()

                first = get_spotify_client()
                second = get_spotify_client()

            self.assertIs(first, second)
            oauth_mock.assert_called_once()
            spotify_mock.assert_called_once()
        finally:
            media_actions.sp = original_sp

    def test_spotify_client_creation_failure_is_safe(self):
        original_sp = media_actions.sp
        media_actions.sp = None
        try:
            with (
                patch.object(media_actions, "SPOTIFY_CLIENT_ID", "id"),
                patch.object(media_actions, "SPOTIFY_CLIENT_SECRET", "secret"),
                patch.object(media_actions.spotipy, "Spotify", side_effect=OSError("auth store unavailable")),
            ):
                result = get_spotify_client()

            self.assertIsNone(result)
            self.assertIsNone(media_actions.sp)
        finally:
            media_actions.sp = original_sp

    def test_media_action_reports_missing_spotify_configuration(self):
        spoken = []
        original_sp = media_actions.sp
        media_actions.sp = None
        try:
            with patch.object(media_actions, "SPOTIFY_CLIENT_ID", None), patch.object(media_actions, "SPOTIFY_CLIENT_SECRET", None):
                result = media_actions.handle_media_action("spotify_play", {}, {"speak": spoken.append, "logger": DummyLogger()})

            self.assertTrue(result)
            self.assertIn("Spotify credentials not found. Spotify integration disabled.", spoken[0])
        finally:
            media_actions.sp = original_sp

    def test_spotify_can_be_disabled_by_environment_flag(self):
        with patch.dict("os.environ", {"JARVIS_ENABLE_SPOTIFY": "false"}):
            self.assertFalse(media_actions.spotify_enabled())

    def test_media_actions_execute_playback_controls_and_volume(self):
        client = unittest.mock.Mock()
        spoken = []

        with patch.object(media_actions, "get_spotify_client", return_value=client):
            for action in ["spotify_play", "spotify_pause", "spotify_next", "spotify_prev"]:
                self.assertTrue(media_actions.handle_media_action(action, {}, {"speak": spoken.append, "logger": DummyLogger()}))
            self.assertTrue(
                media_actions.handle_media_action("spotify_volume", {"level": 250}, {"speak": spoken.append, "logger": DummyLogger()})
            )

        client.start_playback.assert_called_once_with()
        client.pause_playback.assert_called_once_with()
        client.next_track.assert_called_once_with()
        client.previous_track.assert_called_once_with()
        client.volume.assert_called_once_with(100)

    def test_media_search_and_current_playback_success_and_empty_states(self):
        client = unittest.mock.Mock()
        spoken = []
        client.search.side_effect = [
            {"tracks": {"items": [{"uri": "spotify:track:1", "name": "Song", "artists": [{"name": "Artist"}]}]}},
            {"tracks": {"items": []}},
        ]
        client.current_playback.side_effect = [
            {"is_playing": True, "item": {"name": "Song", "artists": [{"name": "Artist"}]}},
            {"is_playing": False},
        ]

        with patch.object(media_actions, "get_spotify_client", return_value=client):
            self.assertTrue(
                media_actions.handle_media_action("spotify_search", {"query": "song"}, {"speak": spoken.append, "logger": DummyLogger()})
            )
            self.assertTrue(
                media_actions.handle_media_action("spotify_search", {"query": "missing"}, {"speak": spoken.append, "logger": DummyLogger()})
            )
            self.assertTrue(media_actions.handle_media_action("spotify_current", {}, {"speak": spoken.append, "logger": DummyLogger()}))
            self.assertTrue(media_actions.handle_media_action("spotify_current", {}, {"speak": spoken.append, "logger": DummyLogger()}))

        client.start_playback.assert_called_once_with(uris=["spotify:track:1"])
        self.assertIn("Playing Song", spoken[0])
        self.assertIn("Couldn't find missing", spoken[1])
        self.assertIn("Currently playing Song", spoken[2])
        self.assertIn("Nothing is playing", spoken[3])

    def test_media_action_handles_unknown_and_spotify_errors(self):
        client = unittest.mock.Mock()
        client.start_playback.side_effect = RuntimeError("device unavailable")
        spoken = []
        logger = DummyLogger()

        with patch.object(media_actions, "get_spotify_client", return_value=client):
            self.assertIsNone(media_actions.handle_media_action("spotify_shuffle", {}, {"speak": spoken.append, "logger": logger}))
            self.assertTrue(media_actions.handle_media_action("spotify_play", {}, {"speak": spoken.append, "logger": logger}))
            self.assertIsNone(media_actions.handle_media_action("open_app", {}, {"speak": spoken.append, "logger": logger}))

        self.assertTrue(any(level == "warning" for level, _ in logger.messages))
        self.assertFalse(any(level == "exception" for level, _ in logger.messages))
        self.assertTrue(any("couldn't complete" in item.lower() for item in spoken))


if __name__ == "__main__":
    unittest.main()
