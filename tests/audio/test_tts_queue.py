from unittest import TestCase

from open_jarvis.audio.tts_queue import TTSQueue


class TTSQueueTest(TestCase):
    def test_enqueue_and_drain_playback_in_order(self):
        spoken = []
        queue = TTSQueue(playback=spoken.append)

        queue.enqueue("first")
        queue.enqueue("second")
        queue.drain_all()

        self.assertEqual(spoken, ["first", "second"])
        self.assertFalse(queue.is_speaking())

    def test_clear_removes_pending_items(self):
        queue = TTSQueue(playback=lambda text: None)
        queue.enqueue("first")
        queue.enqueue("second")

        result = queue.clear()

        self.assertEqual(result["cleared"], 2)
        self.assertEqual(queue.pending_count(), 0)

    def test_stop_prevents_pending_playback(self):
        spoken = []
        queue = TTSQueue(playback=spoken.append)
        queue.enqueue("first")

        queue.stop()
        result = queue.drain_next()

        self.assertEqual(result["status"], "stopped")
        self.assertEqual(spoken, [])

    def test_tts_failure_isolated(self):
        queue = TTSQueue(playback=lambda text: (_ for _ in ()).throw(RuntimeError("audio offline")))
        queue.enqueue("hello")

        result = queue.drain_next()

        self.assertEqual(result["status"], "failed")
        self.assertFalse(queue.is_speaking())
