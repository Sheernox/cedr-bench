import json
import os
import tempfile
import unittest

from findr.match import search
from findr.nodes import And, Compare, Not, Or, Term
from findr.parser import ParseError, parse
from findr.render import render
from findr.store import SavedSearch, StoreError, add_search, load_searches
from findr.suggest import similar_to

RECORDS = [
    {"id": 1, "title": "Q3 invoice", "status": "open", "owner": "ana", "size": 12},
    {"id": 2, "title": "Q3 report", "status": "closed", "owner": "ben k", "size": 4},
    {"id": 3, "title": 'say "hi"', "status": "open", "owner": "cy", "size": 30},
]


class ParseTest(unittest.TestCase):
    def test_terms(self):
        self.assertEqual(parse("status:open"), Term("status", "open"))
        self.assertEqual(parse("size>=10"), Compare("size", ">=", "10"))
        self.assertEqual(parse("a b OR c"), Or((And((Term(None, "a"), Term(None, "b"))), Term(None, "c"))))
        self.assertEqual(parse("-a"), Not(Term(None, "a")))

    def test_quotes(self):
        self.assertEqual(parse('title:"say \\"hi\\""'), Term("title", 'say "hi"'))
        self.assertEqual(parse('path:"C:\\temp"'), Term("path", "C:\\temp"))

    def test_errors(self):
        for text in ["", "a:", "(a", 'x:"open', "size>ten", "9x:1"]:
            with self.assertRaises(ParseError, msg=text):
                parse(text)


class MatchTest(unittest.TestCase):
    def test_search(self):
        hits = search(parse('Q3 -owner:"ben k"'), RECORDS)
        self.assertEqual([r["id"] for r in hits], [1])
        hits = search(parse("size>10 status:open"), RECORDS)
        self.assertEqual([r["id"] for r in hits], [1, 3])


class RenderTest(unittest.TestCase):
    def test_round_trip(self):
        for text in ['status:open -owner:"ben k"', "(a OR b) c", 'title:"say \\"hi\\""', "size<=4.5", 'x:"OR"']:
            node = parse(text)
            self.assertEqual(parse(render(node)), node, text)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "searches.json")

    def test_add_and_load(self):
        add_search(self.path, "mine", parse("owner:ana status:open"))
        add_search(self.path, "big", parse("size>20"))
        loaded = load_searches(self.path)
        self.assertEqual([s.name for s in loaded], ["mine", "big"])
        self.assertEqual(loaded[0].node(), parse("owner:ana status:open"))

    def test_version_0(self):
        with open(self.path, "w") as handle:
            json.dump(["status:open", "owner:ana"], handle)
        loaded = load_searches(self.path)
        self.assertEqual(loaded, [SavedSearch("search-1", "status:open"), SavedSearch("search-2", "owner:ana")])

    def test_unknown_version(self):
        with open(self.path, "w") as handle:
            json.dump({"version": 7, "searches": []}, handle)
        with self.assertRaises(StoreError):
            load_searches(self.path)


class SuggestTest(unittest.TestCase):
    def test_similar(self):
        query = similar_to({"owner": "ben k", "status": "open", "path": ""})
        self.assertEqual(query, 'owner:"ben k" status:"open"')
        self.assertEqual([r["id"] for r in search(parse(query), RECORDS)], [])


if __name__ == "__main__":
    unittest.main()
