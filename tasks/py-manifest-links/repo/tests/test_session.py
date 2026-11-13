import json
from pathlib import Path
import unittest
from packtree.session import Session
from packtree.cli import open_session, main
from packtree.commands import Commands, CommandError

class SessionTest(unittest.TestCase):
    def setUp(self):
        path=Path(__file__).resolve().parents[1]/"examples/session.json"
        self.document=json.loads(path.read_text())
        self.session=open_session(self.document)
    def test_commands_reject_unknown(self):
        with self.assertRaises(CommandError):Commands(self.session).execute("unknown",{})
    def test_report_is_detached(self):
        command=Commands(self.session)
        original=command.execute("report",{})
        result=command.execute("report",{})
        if result:result[0]["tamper"]=True
        self.assertEqual(command.execute("report",{}),original)
    def test_read_only_commands(self):
        before=self.session.document()
        command=Commands(self.session)
        for name in ["totals","views","report","audit","snapshot"]:
            command.execute(name,{})
        self.assertEqual(self.session.document(),before)
    def test_command_arguments(self):
        with self.assertRaises(CommandError):Commands(self.session).execute("totals",{"view":"x"})
    def test_report_pagination(self):
        command=Commands(self.session)
        self.assertEqual(command.execute("report",{"page":100}),[])
    def test_view_restore(self):
        from packtree.views import ViewCatalog
        views=ViewCatalog.restore(self.session.views.export())
        self.assertEqual(views.export(),self.session.views.export())
    def test_json_snapshot(self):
        snapshot=self.session.document()
        self.assertEqual(json.loads(json.dumps(snapshot)),snapshot)
    def test_audit_initially_empty(self):
        self.assertEqual(Commands(self.session).execute("audit",{}),[])
