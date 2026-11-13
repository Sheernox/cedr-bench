import unittest
from spanboard.timeline import build
from spanboard.csvview import export_csv

def row(id, start, end, value="v", priority=0, revision=0, channel="main", deleted=False):
    return dict(id=id, start=start, end=end, value=value, priority=priority, revision=revision, channel=channel, deleted=deleted)

class TimelineTest(unittest.TestCase):
    def test_single(self):
        self.assertEqual(build([row("a", 0, 10)], 2, 8), [dict(channel="main", start=2, end=8, value="v", source="a")])
    def test_empty(self):
        self.assertEqual(export_csv([], 0, 10), "channel,start,end,value,source\n")
