"""Stable catalog exports consumed by scripts and terminal commands."""
from __future__ import annotations
from collections.abc import Iterable
from .model import Entry
from recordkit.table import Column, render, delimited
from recordkit.jsonio import pretty
from recordkit.query import select

COLUMNS = (Column("space", "SPACE"), Column("start", "START", 20, "right"), Column("end", "END", 20, "right"),
           Column("revision", "REVISION", 12, "right"), Column("value", "VALUE", 60))

def rows(entries: Iterable[Entry], query: str = "") -> list[dict[str, object]]:
    values = [entry.document() for entry in entries if not entry.deleted]
    return [dict(row) for row in select(values, query)]

def export(entries: Iterable[Entry], format: str = "json", query: str = "") -> str:
    data = rows(entries, query)
    if format == "json":
        return pretty(data)
    if format == "csv":
        return delimited(data, COLUMNS)
    if format == "table":
        return render(data, COLUMNS)
    raise ValueError("format must be json, csv or table")
