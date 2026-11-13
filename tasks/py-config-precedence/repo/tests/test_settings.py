import os
import tempfile
import unittest

from notify.settings import load_settings
from notify.sources import ConfigError


def write_config(text: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False)
    handle.write(text)
    handle.close()
    return handle.name


class PrecedenceTest(unittest.TestCase):
    def test_defaults(self):
        settings = load_settings([], {})
        self.assertEqual(settings.channel, "#general")
        self.assertEqual(settings.batch_size, 50)

    def test_flag_beats_env_and_file(self):
        path = write_config('[notify]\nchannel = "#file"\n')
        self.addCleanup(os.unlink, path)
        settings = load_settings(["--channel", "#flag"], {"NOTIFY_CHANNEL": "#env"}, path)
        self.assertEqual(settings.channel, "#flag")

    def test_env_beats_file(self):
        path = write_config("[notify]\nretries = 5\n")
        self.addCleanup(os.unlink, path)
        settings = load_settings([], {"NOTIFY_RETRIES": "7"}, path)
        self.assertEqual(settings.retries, 7)

    def test_env_boolean(self):
        settings = load_settings([], {"NOTIFY_QUIET": "true"})
        self.assertTrue(settings.quiet)

    def test_unknown_key(self):
        path = write_config("[notify]\ncolour = 'red'\n")
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ConfigError):
            load_settings([], {}, path)


if __name__ == "__main__":
    unittest.main()
