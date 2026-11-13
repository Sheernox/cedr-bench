"""Resolve imported time intervals into an installed schedule index."""
from __future__ import annotations
from collections.abc import Iterable
from .model import Entry

def reduce_entries(entries: Iterable[Entry]) -> dict[tuple[str, int, int], Entry]:
    result: dict[tuple[str, int, int], Entry] = {}
    for entry in entries:
        if not entry.deleted:
            result[entry.identity] = entry
    return result
