"""Search and filter across current in-memory notes."""
from __future__ import annotations
from .model import Note, Vault
from recordkit.query import select

def documents(vault: Vault) -> list[dict[str, object]]:
    return [{"id": n.id, "title": n.title, "body": n.body, "labels": n.labels,
             "pinned": n.pinned, "archived": n.archived} for n in vault.notes]

def search(vault: Vault, query: str = "", include_archived: bool = False) -> list[Note]:
    identities = {row["id"] for row in select(documents(vault), query)}
    return [note.clone() for note in vault.notes if note.id in identities
            and (include_archived or not note.archived)]

def by_label(vault: Vault) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for note in vault.notes:
        for label in dict.fromkeys(note.labels):
            result.setdefault(label, []).append(note.id)
    return result
