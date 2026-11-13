"""Read-only schedule previews for the import command."""
from __future__ import annotations
from collections.abc import Iterable
from .model import Entry, decode

def preview(snapshot: list[dict[str, object]], pages: Iterable[Iterable[Entry]]) -> list[Entry]:
    index = {decode(row).identity:decode(row) for row in snapshot}
    for page in pages:
        for entry in page:
            if entry.deleted:
                index.pop(entry.identity,None)
            else:
                index[entry.identity] = entry
    return [entry for _,entry in sorted(index.items()) if not entry.deleted]
