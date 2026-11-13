import unittest
import tempfile
from pathlib import Path
from release.rules import Policy
from release.scan import walk
from release.fast import inventory
from release.build import build
from release.verify import verify,Required

class SelectionTests(unittest.TestCase):
    def test_basename(self):
        self.assertFalse(Policy(["*.tmp"]).included("a/x.tmp"))
        self.assertTrue(Policy(["*.tmp"]).included("a/x.txt"))

    def test_plain_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/"src";root.mkdir()
            (root/"a.txt").write_text("a")
            (root/"x.tmp").write_text("x")
            output=Path(directory)/"bundle.zip"
            rows=build(root,["*.tmp"],output)
            self.assertEqual([row["name"] for row in rows],["a.txt"])
            self.assertEqual(inventory(root,Policy(["*.tmp"])),["a.txt"])
            self.assertTrue(verify(output.read_bytes(),[Required("a.txt",1)]).ok)

if __name__ == "__main__": unittest.main()
