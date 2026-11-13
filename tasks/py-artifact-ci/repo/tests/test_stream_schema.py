import unittest
from recordkit import schema,stream
from recordkit.validation import Invalid

class SchemaTests(unittest.TestCase):
    def test_nested_error_paths(self):
        validator=schema.record({"rows":schema.Field(schema.array(schema.record({
            "name":schema.Field(schema.string),"size":schema.Field(schema.bounded(0,100))
        })))})
        with self.assertRaises(Invalid) as context:
            schema.validate({"rows":[{"name":"x","size":-1}]},validator)
        self.assertEqual(context.exception.path,"$.rows[0].size")
        self.assertEqual(schema.validate({"rows":[]},validator),{"rows":[]})

    def test_default_values_are_owned(self):
        validator=schema.record({"labels":schema.Field(schema.array(schema.string),False,[])})
        first=schema.validate({},validator)
        second=schema.validate({},validator)
        first["labels"].append("borrowed")
        self.assertEqual(second,{"labels":[]})

    def test_unknown_field_policies(self):
        fields={"name":schema.Field(schema.string)}
        value={"name":"x","metadata":{"labels":[]}}
        with self.assertRaises(Invalid): schema.validate(value,schema.record(fields))
        self.assertEqual(schema.validate(value,schema.record(fields,"drop")),{"name":"x"})
        preserved=schema.validate(value,schema.record(fields,"preserve"))
        preserved["metadata"]["labels"].append("owned")
        self.assertEqual(value["metadata"]["labels"],[])

    def test_discriminated_alternatives(self):
        validator=schema.one_of(
            schema.record({"kind":schema.Field(schema.literal("text")),"value":schema.Field(schema.string)}),
            schema.record({"kind":schema.Field(schema.literal("number")),"value":schema.Field(schema.number)}))
        self.assertEqual(schema.validate({"kind":"text","value":""},validator),{"kind":"text","value":""})
        self.assertEqual(schema.validate({"kind":"number","value":0},validator),{"kind":"number","value":0})
        with self.assertRaises(Invalid): schema.validate({"kind":"number","value":False},validator)

    def test_unique_structures(self):
        validator=schema.array(schema.dictionary(schema.number),True)
        with self.assertRaises(Invalid): schema.validate([{"a":1,"b":2},{"b":2,"a":1}],validator)
        self.assertEqual(schema.validate([{"a":1},{"a":2}],validator),[{"a":1},{"a":2}])

    def test_nullable_and_transform(self):
        validator=schema.nullable(schema.transform(schema.string,str.upper))
        self.assertIsNone(schema.validate(None,validator))
        self.assertEqual(schema.validate("hello",validator),"HELLO")
        with self.assertRaises(Invalid): schema.validate(0,validator)

    def test_literal_distinguishes_boolean(self):
        with self.assertRaises(Invalid): schema.validate(True,schema.literal(1))
        self.assertEqual(schema.validate(1,schema.literal(1)),1)
        with self.assertRaises(ValueError): schema.bounded(5,1)
        with self.assertRaises(ValueError): schema.one_of()
        with self.assertRaises(ValueError): schema.record({},"other")

class StreamTests(unittest.TestCase):
    def test_chunks_preserve_tail(self):
        self.assertEqual(list(stream.chunks(iter(range(8)),3)),[[0,1,2],[3,4,5],[6,7]])
        self.assertEqual(list(stream.chunks([],3)),[])
        with self.assertRaises(ValueError): list(stream.chunks([1],0))

    def test_sliding_window(self):
        self.assertEqual(list(stream.window(range(5),3)),[(0,1,2),(1,2,3),(2,3,4)])
        self.assertEqual(list(stream.window([1],2)),[])
        with self.assertRaises(ValueError): list(stream.window([1],0))

    def test_adjacent_groups_preserve_repeated_runs(self):
        self.assertEqual(list(stream.adjacent_groups("aabbba",lambda x:x)),
                         [("a",["a","a"]),("b",["b","b","b"]),("a",["a"])])
        self.assertEqual(list(stream.adjacent_groups([],lambda x:x)),[])

    def test_merge_ties_are_stable_by_source(self):
        left=[(1,"a"),(2,"b")]
        right=[(1,"c"),(3,"d")]
        self.assertEqual(list(stream.merge_sorted([iter(left),[],iter(right)],lambda x:x[0])),
                         [(1,"a"),(1,"c"),(2,"b"),(3,"d")])

    def test_take_does_not_overconsume(self):
        values=iter(range(5))
        self.assertEqual(list(stream.take(values,2)),[0,1])
        self.assertEqual(next(values),2)
        self.assertEqual(list(stream.take([],5)),[])
        with self.assertRaises(ValueError): list(stream.take([], -1))

    def test_recent_dedup_is_bounded(self):
        self.assertEqual(list(stream.unique_recent("abacba",lambda x:x,2)),list("abca"))
        with self.assertRaises(ValueError): list(stream.unique_recent([],lambda x:x,0))

    def test_partition(self):
        self.assertEqual(stream.partition(range(5),lambda x:x%2==0),([0,2,4],[1,3]))
        self.assertEqual(stream.partition([],bool),([],[]))




class StreamBoundaryTests(unittest.TestCase):
    def test_merge_accepts_noncomparable_payloads(self):
        left=[{"key":1,"value":[]}]
        right=[{"key":1,"value":{}}]
        self.assertEqual(list(stream.merge_sorted([left,right],lambda item:item["key"])),left+right)

    def test_groups_allow_none_as_key(self):
        self.assertEqual(list(stream.adjacent_groups([1,2],lambda item:None)),[(None,[1,2])])

    def test_take_zero_does_not_advance(self):
        values=iter([1,2])
        self.assertEqual(list(stream.take(values,0)),[])
        self.assertEqual(next(values),1)

    def test_dictionary_reports_bad_child(self):
        with self.assertRaises(Invalid) as context:
            schema.validate({"size":False},schema.dictionary(schema.number))
        self.assertEqual(context.exception.path,"$.size")

    def test_number_rejects_nonfinite_values(self):
        for value in [float("inf"),float("nan"),"12"]:
            with self.assertRaises(Invalid): schema.validate(value,schema.number)

if __name__ == "__main__": unittest.main()
