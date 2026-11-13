import unittest

from notify.digest import build_digest, delivery_attempts
from notify.settings import Settings


def settings(**overrides):
    values = dict(
        channel="#general",
        batch_size=2,
        retries=3,
        timeout=10.0,
        quiet=False,
        dry_run=True,
        subject_prefix="[digest]",
    )
    values.update(overrides)
    return Settings(**values)


class DigestTest(unittest.TestCase):
    def test_batches(self):
        messages = build_digest(["a", "b", "c"], settings())
        self.assertEqual(len(messages), 2)
        self.assertTrue(messages[0].startswith("[digest] 2 updates (1/2)"))

    def test_zero_batch_size_sends_one_message(self):
        messages = build_digest(["a", "b", "c"], settings(batch_size=0))
        self.assertEqual(messages, ["[digest] 3 updates\n- a\n- b\n- c"])

    def test_attempts(self):
        self.assertEqual(delivery_attempts(settings(retries=0)), 1)


if __name__ == "__main__":
    unittest.main()
