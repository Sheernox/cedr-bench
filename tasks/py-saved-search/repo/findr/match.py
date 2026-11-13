"""Evaluate a parsed search against records (mappings of field to value)."""

from __future__ import annotations

import operator
from collections.abc import Iterable, Mapping

from .nodes import And, Compare, Node, Not, Or, Term

Record = Mapping[str, object]

_OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}


def matches(node: Node, record: Record) -> bool:
    if isinstance(node, Term):
        needle = node.value.casefold()
        if node.field is None:
            return any(needle in _text(value) for value in record.values())
        return node.field in record and needle in _text(record[node.field])
    if isinstance(node, Compare):
        number = _number(record.get(node.field))
        return number is not None and _OPS[node.op](number, float(node.number))
    if isinstance(node, Not):
        return not matches(node.item, record)
    if isinstance(node, And):
        return all(matches(item, record) for item in node.items)
    if isinstance(node, Or):
        return any(matches(item, record) for item in node.items)
    raise TypeError(f"not a search node: {node!r}")


def search(node: Node, records: Iterable[Record]) -> list[Record]:
    return [record for record in records if matches(node, record)]


def _text(value: object) -> str:
    return "" if value is None else str(value).casefold()


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
