"""A small report-filter language, distinct from the domain import protocol.

Filters are JSON objects. Compiling validates even branches that would be
short-circuited at execution, so malformed saved views cannot hide errors.
"""
from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
import re
Predicate = Callable[[Mapping], bool]

class FilterError(ValueError):
    """A report filter is malformed."""

def compile_filter(spec: dict, *, depth: int = 0) -> Predicate:
    if depth > 20 or not isinstance(spec, dict):
        raise FilterError("invalid or excessively nested filter")
    if not spec:
        return lambda row: True
    if set(spec) == {"all"} or set(spec) == {"any"}:
        key = next(iter(spec))
        children = spec[key]
        if not isinstance(children, list):
            raise FilterError("compound filter needs a list")
        predicates = [compile_filter(child, depth=depth + 1) for child in children]
        if key == "all":
            return lambda row: all(p(row) for p in predicates)
        return lambda row: any(p(row) for p in predicates)
    if set(spec) == {"not"}:
        child = compile_filter(spec["not"], depth=depth + 1)
        return lambda row: not child(row)
    if set(spec) != {"field", "op", "value"}:
        raise FilterError("expected field, op and value")
    field, op, value = spec["field"], spec["op"], deepcopy(spec["value"])
    if not isinstance(field, str) or not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", field):
        raise FilterError("invalid field name")
    if op == "eq":
        return lambda row: field in row and type(row[field]) is type(value) and row[field] == value
    if op == "ne":
        return lambda row: field not in row or type(row[field]) is not type(value) or row[field] != value
    if op == "contains":
        if not isinstance(value, str):
            raise FilterError("contains needs text")
        return lambda row: isinstance(row.get(field), str) and value.casefold() in row[field].casefold()
    if op == "in":
        if not isinstance(value, list):
            raise FilterError("in needs a list")
        return lambda row: field in row and any(type(row[field]) is type(v) and row[field] == v for v in value)
    if op == "range":
        if not isinstance(value, list) or len(value) != 2 or any(type(x) is not int for x in value) or value[0] > value[1]:
            raise FilterError("range needs two ordered integers")
        return lambda row: type(row.get(field)) is int and value[0] <= row[field] <= value[1]
    raise FilterError("unknown filter operation")

def select(rows: Iterable[Mapping], spec: dict) -> list[dict]:
    predicate = compile_filter(spec)
    return [deepcopy(dict(row)) for row in rows if predicate(row)]

def project(rows: Iterable[Mapping], fields: tuple[str, ...]) -> list[dict]:
    if len(set(fields)) != len(fields):
        raise FilterError("duplicate projected field")
    return [{key: deepcopy(row[key]) for key in fields if key in row} for row in rows]

def distinct(rows: Iterable[Mapping], field: str) -> list:
    values = []
    for row in rows:
        if field in row and not any(type(v) is type(row[field]) and v == row[field] for v in values):
            values.append(deepcopy(row[field]))
    return values

def summary(spec: dict) -> str:
    compile_filter(spec)
    if not spec:
        return "all records"
    if "all" in spec or "any" in spec:
        key = "all" if "all" in spec else "any"
        return "(" + (" AND " if key == "all" else " OR ").join(summary(s) for s in spec[key]) + ")"
    if "not" in spec:
        return "NOT (" + summary(spec["not"]) + ")"
    return f"{spec['field']} {spec['op']} {spec['value']!r}"
