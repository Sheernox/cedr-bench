"""Deterministic tabular reports used by the terminal and static HTML views."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from html import escape

@dataclass(frozen=True)
class Column:
    key: str
    title: str
    width: int = 24
    align: str = "left"
    def __post_init__(self) -> None:
        if self.width < 3 or self.align not in ("left", "right"):
            raise ValueError("invalid column width or alignment")

def cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(cell(x) for x in value)
    return str(value)

def one_line(text: str) -> str:
    return " ".join(text.split())

def truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[:width - 3] + "..."

def plain(rows: Iterable[Mapping], columns: tuple[Column, ...], *, header: bool = True) -> str:
    def render(values: list[str]) -> str:
        out = []
        for text, column in zip(values, columns):
            text = truncate(one_line(text), column.width)
            out.append(text.rjust(column.width) if column.align == "right" else text.ljust(column.width))
        return " | ".join(out).rstrip()
    result = []
    if header:
        result.append(render([c.title for c in columns]))
        result.append("-+-".join("-" * c.width for c in columns))
    result.extend(render([cell(row.get(c.key)) for c in columns]) for row in rows)
    return "\n".join(result) + ("\n" if result else "")

def html(rows: Iterable[Mapping], columns: tuple[Column, ...], caption: str) -> str:
    head = "".join("<th scope=\"col\">" + escape(c.title) + "</th>" for c in columns)
    body = []
    for row in rows:
        body.append("<tr>" + "".join("<td>" + escape(cell(row.get(c.key))) + "</td>" for c in columns) + "</tr>")
    return "<table><caption>" + escape(caption) + "</caption><thead><tr>" + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table>"

def page(rows: Iterable[Mapping], offset: int, limit: int) -> list[dict]:
    if type(offset) is not int or type(limit) is not int or offset < 0 or limit < 0:
        raise ValueError("offset and limit must be nonnegative integers")
    from itertools import islice
    return [dict(row) for row in islice(rows, offset, offset + limit)]

def totals(rows: Iterable[Mapping], fields: tuple[str, ...]) -> dict[str, int]:
    result = dict.fromkeys(fields, 0)
    for row in rows:
        for field in fields:
            value = row.get(field, 0)
            if type(value) is not int:
                raise ValueError("total field must be integer: " + field)
            result[field] += value
    return result

def histogram(rows: Iterable[Mapping], field: str) -> list[dict]:
    counts: dict[str, int] = {}
    for row in rows:
        label = cell(row.get(field))
        counts[label] = counts.get(label, 0) + 1
    return [{"label": label, "count": count} for label, count in sorted(counts.items())]

def ordered(rows: Iterable[Mapping], field: str, *, descending: bool = False) -> list[dict]:
    materialized = [dict(row) for row in rows]
    return sorted(materialized, key=lambda r: (r.get(field) is not None, cell(r.get(field))), reverse=descending)
