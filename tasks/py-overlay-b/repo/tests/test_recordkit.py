"""Library behavior used by the offline command adapters."""
import json
import tempfile
import unittest
from pathlib import Path
from recordkit import jsonio, validation, paths, query, table, audit, stats
from recordkit.archive import Member,pack,unpack,extract
from recordkit.config import Preferences,decode,overlay,serialize,apply_environment
from recordkit.transaction import begin,editing,Conflict,backup,restore
from recordkit.report import Report,combine

class JsonTests(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(jsonio.canonical({"b":2,"a":"é"}),b'{"a":"\xc3\xa9","b":2}')
        self.assertEqual(jsonio.fingerprint({"a":1,"b":2}),jsonio.fingerprint({"b":2,"a":1}))

    def test_reject_invalid(self):
        with self.assertRaises(jsonio.DocumentError): jsonio.decode("{broken")
        with self.assertRaises(ValueError): jsonio.canonical(float("nan"))

    def test_file_and_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"rows.jsonl"
            self.assertEqual(jsonio.write_lines(path,[{"x":1},{"x":2}]),2)
            self.assertEqual(list(jsonio.read_lines(path)),[{"x":1},{"x":2}])
            jsonio.atomic_write(path,{"value":[]})
            self.assertEqual(jsonio.read(path),{"value":[]})

class ValidationTests(unittest.TestCase):
    def test_types(self):
        self.assertEqual(validation.integer(0,minimum=0),0)
        for value in [True,1.5,"2"]:
            with self.assertRaises(validation.Invalid): validation.integer(value)
        self.assertFalse(validation.boolean(False))
        self.assertEqual(validation.strings(["", "é"]),["","é"])

    def test_keys(self):
        with self.assertRaises(validation.Invalid): validation.required({},"x")
        with self.assertRaises(validation.Invalid): validation.reject_unknown({"x":1},{"y"})
        with self.assertRaises(validation.Invalid): validation.unique(["a","a"])

class PathTests(unittest.TestCase):
    def test_portable(self):
        self.assertEqual(paths.relative_name("./a/b"),"a/b")
        self.assertEqual(paths.parent_names("a/b/c"),("a","a/b"))
        self.assertEqual(paths.common_prefix(["a/b/c","a/b/d"]),"a/b")
        self.assertEqual(paths.replace_suffix("a/b.json",".txt"),"a/b.txt")

    def test_escape(self):
        for value in ["/tmp/file","../file","a/../../b","C:/file","a\\b",""]:
            with self.assertRaises(ValueError): paths.relative_name(value)

class QueryTests(unittest.TestCase):
    def test_select(self):
        rows=[{"title":"Alpha Beta","tag":["work"]},{"title":"Gamma","tag":["home"]}]
        self.assertEqual(query.select(rows,'title:"alpha beta" -tag:home'),rows[:1])
        self.assertEqual(query.select(rows,"HOME"),rows[1:])

    def test_invalid_filter(self):
        for raw in ["field:","-",'"unterminated']:
            with self.assertRaises(ValueError): query.parse(raw)

    def test_order_and_project(self):
        rows=[{"id":"b","x":1},{"id":"A","x":2}]
        self.assertEqual(query.order(rows,"id"),rows[::-1])
        self.assertEqual(query.project(rows[0],("id","missing")),{"id":"b","missing":None})

class TableTests(unittest.TestCase):
    def test_csv_escaping(self):
        columns=[table.Column("x","X"),table.Column("n","N",8,"right")]
        raw=table.delimited([{"x":"a,b","n":2}],columns)
        self.assertEqual(table.parse_delimited(raw,["x","n"]),[{"x":"a,b","n":"2"}])
        self.assertIn('"a,b"',raw)

    def test_fixed_width(self):
        columns=[table.Column("x","X",4),table.Column("n","N",4,"right")]
        raw=table.render([{"x":"abcdefgh","n":2}],columns)
        self.assertEqual(raw,"X     N\nabc~  2\n")
        self.assertEqual(table.plain("a\nb\tc"),"a b c")

class AuditTests(unittest.TestCase):
    def test_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"audit.jsonl"
            first=audit.append(path,"save",{"n":1},"2020-01-01T00:00:00Z")
            second=audit.append(path,"load",{},"2020-01-01T00:00:01Z")
            self.assertEqual(second.previous,first.digest())
            self.assertEqual(audit.verify(audit.load(path)),second.digest())
            self.assertEqual(audit.summarize(audit.load(path)),{"save":1,"load":1})

class StatsTests(unittest.TestCase):
    def test_streaming_moments(self):
        moments=stats.Moments()
        for value in [1,2,3]: moments.add(value)
        self.assertEqual(moments.mean,2)
        self.assertAlmostEqual(moments.variance,2/3)
        with self.assertRaises(ValueError): moments.add(float("inf"))

    def test_counter(self):
        left=stats.Counter();left.add("b",2)
        right=stats.Counter();right.add("a",2);left.merge(right)
        self.assertEqual(left.top(1),[("a",2)])

class ArchiveTests(unittest.TestCase):
    def test_roundtrip_and_determinism(self):
        members=[Member("x/b",b"two",True),Member("a",b"one")]
        self.assertEqual(pack(members),pack(reversed(members)))
        self.assertEqual(unpack(pack(members)),list(reversed(members)))
        with self.assertRaises(ValueError): unpack(pack(members),max_bytes=1)

    def test_members(self):
        for members in [[Member("../escape",b"")],[Member("x",b""),Member("x",b"a")],
                        [Member("MANIFEST.json",b"")]]:
            with self.assertRaises(ValueError): pack(members)

    def test_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(extract(pack([Member("a/b",b"data")]),Path(directory)),1)
            self.assertEqual(Path(directory,"a/b").read_bytes(),b"data")

class ConfigTests(unittest.TestCase):
    def test_toml(self):
        import tomllib
        preferences=Preferences("csv",20,True,"audit.jsonl",("id","title"))
        self.assertEqual(decode(tomllib.loads(serialize(preferences))),preferences)
        self.assertEqual(overlay(preferences,{"quiet":False}).quiet,False)

    def test_environment(self):
        preferences=apply_environment(Preferences(),{"APP_QUIET":"false","APP_PAGE_SIZE":"5"},"APP_")
        self.assertEqual(preferences.page_size,5)
        self.assertFalse(preferences.quiet)
        with self.assertRaises(ValueError): apply_environment(Preferences(),{"APP_QUIET":"maybe"},"APP_")

class TransactionTests(unittest.TestCase):
    def test_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"doc.json"
            jsonio.atomic_write(path,{"a":1})
            edit=begin(path)
            jsonio.atomic_write(path,{"a":2})
            with self.assertRaises(Conflict): edit.commit()
            self.assertEqual(jsonio.read(path),{"a":2})

    def test_commit_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"doc.json";copy=Path(directory)/"backup.json"
            with editing(path,{"a":[]}) as edit: edit.value["a"].append(1)
            expected=backup(path,copy)
            jsonio.atomic_write(path,{"a":2})
            restore(copy,path,expected)
            self.assertEqual(jsonio.read(path),{"a":[1]})

    def test_failed_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"doc.json"
            jsonio.atomic_write(path,{"a":1})
            def reject(value): raise ValueError("bad document")
            with self.assertRaises(ValueError):
                with editing(path,validate=reject) as edit: edit.value["a"]=None
            self.assertEqual(jsonio.read(path),{"a":1})

class ReportTests(unittest.TestCase):
    def test_combining(self):
        left=Report(checked=2);left.add("W01","x","warning","warning")
        right=Report(checked=3);right.add("E01","y","error")
        result=combine([left,right])
        self.assertFalse(result.ok)
        self.assertEqual(result.checked,5)
        self.assertEqual(result.counts(),{"info":0,"warning":1,"error":1})
        self.assertEqual(json.loads(result.json())["checked"],5)
        self.assertIn("W01",result.table())

if __name__ == "__main__": unittest.main()
