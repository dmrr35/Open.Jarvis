import unittest
from unittest.mock import patch

from open_jarvis.runtime.process_runner import launch_process, run_command


class ProcessRunnerTests(unittest.TestCase):
    def test_launch_process_passes_argument_list(self):
        with patch("open_jarvis.runtime.process_runner.subprocess.Popen") as popen_mock:
            launch_process(["notepad.exe"])

        popen_mock.assert_called_once_with(["notepad.exe"], shell=False)

    def test_run_command_disables_shell_by_default(self):
        with patch("open_jarvis.runtime.process_runner.subprocess.run") as run_mock:
            run_command(["shutdown", "/s", "/t", "5"])

        run_mock.assert_called_once_with(["shutdown", "/s", "/t", "5"], check=False, shell=False)


if __name__ == "__main__":
    unittest.main()
