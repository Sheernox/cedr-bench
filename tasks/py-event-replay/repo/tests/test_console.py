import json
from pathlib import Path
import unittest
from streamdesk.cli import open_session
from streamdesk.commands import Commands
from streamdesk.cursors import CursorError
from streamdesk.views import View

class ConsolePagingTest(unittest.TestCase):
    def setUp(self):
        path=Path(__file__).resolve().parents[1]/"examples/session.json"
        self.session=open_session(json.loads(path.read_text()))
        self.commands=Commands(self.session)

    def test_first_report_page(self):
        rows=self.commands.execute("report",{})
        result=self.commands.execute("report-page",{})
        self.assertEqual(result["rows"],rows)
        self.assertEqual(result["total"],len(rows))
        self.assertIsNone(result["next"])

    def test_page_is_detached(self):
        original=self.commands.execute("report",{})
        result=self.commands.execute("report-page",{})
        result["rows"][0]["changed"]=True
        self.assertEqual(self.commands.execute("report",{}),original)

    def test_bad_cursor(self):
        with self.assertRaises(CursorError):
            self.commands.execute("report-page",{"cursor":"invalid"})

    def test_view_can_be_replaced(self):
        old=self.session.views.export()[0]
        view=View.restore({**old,"page_size":3})
        self.session.views.add(view,replace=True)
        self.assertEqual(len(self.commands.execute("report",{})),3)

    def test_unknown_view(self):
        with self.assertRaises(ValueError):
            self.commands.execute("report",{"view":"missing"})

    def test_invalid_page(self):
        for page in [-1,True,1.5]:
            with self.assertRaises(ValueError):
                self.commands.execute("report",{"page":page})

    def test_html_report_caption(self):
        from streamdesk.table import Column
        output=self.commands.format_report({},(Column("label","Name"),),"html")
        self.assertIn("<caption>Report</caption>",output)
        self.assertIn('scope="col"',output)

    def test_report_output_format(self):
        with self.assertRaises(ValueError):
            self.commands.format_report({},(),"unknown")

    def test_session_document_detached(self):
        original=self.session.document()
        result=self.commands.execute("snapshot",{})
        result["views"][0]["name"]="changed"
        self.assertEqual(self.session.document(),original)

    def test_filter_all_pages_empty(self):
        self.assertEqual(self.commands.execute("report",{"filter":{"any":[]}}),[])

    def test_query_precompiled_before_data(self):
        with self.assertRaises(ValueError):
            self.commands.execute("report",{"page":100,"filter":{"broken":1}})
