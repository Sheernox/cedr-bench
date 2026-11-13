"""Installed schedules retain history needed for replayed feeds."""
from __future__ import annotations
from collections.abc import Iterable
from copy import deepcopy
from .model import Entry, decode
from .reduce import reduce_entries

class Catalog:
    def __init__(self, entries: Iterable[Entry] = ()) -> None:
        self._index = reduce_entries(entries)

    def ingest(self, entries: Iterable[Entry]) -> None:
        self._index.update(reduce_entries(entries))

    def visible(self, space: str | None = None) -> list[Entry]:
        return [deepcopy(entry) for _, entry in sorted(self._index.items())
                if not entry.deleted and (space is None or entry.space == space)]

    def snapshot(self) -> list[dict[str, object]]:
        return [entry.document() for _, entry in sorted(self._index.items())]

    @classmethod
    def restore(cls, rows: list[dict[str, object]]) -> Catalog:
        return cls(decode(row) for row in rows)

    def lookup(self, space: str, point: int) -> Entry | None:
        for entry in self._index.values():
            if entry.space == space and entry.start <= point < entry.end and not entry.deleted:
                return deepcopy(entry)
        return None
