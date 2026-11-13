"""Merge another vault without changing the destination's record order."""
from __future__ import annotations
from copy import deepcopy
from .model import Vault
from .codec import decode

def merge(destination: Vault, source: Vault, overwrite: bool = False) -> Vault:
    result = deepcopy(destination)
    identities = {note.id for note in result.notes}
    for note in source.notes:
        if note.id not in identities or overwrite:
            result.replace(note)
            identities.add(note.id)
    for key, value in source.extra.items():
        if key not in result.extra:
            result.extra[key] = deepcopy(value)
    return result

def import_document(destination: Vault, document: object, overwrite: bool = False) -> Vault:
    # CLI import used to predate the Store abstraction.
    rows = document["notes"] if isinstance(document, dict) else document
    from .model import Note
    incoming = Vault([Note(row.get("id", f"import-{i}"), row["title"],
                           row.get("body", row.get("text", "")),
                           row.get("labels", [])) for i, row in enumerate(rows, 1)])
    return merge(destination, incoming, overwrite)
