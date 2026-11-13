"""Decode a vault and encode the current revision."""
from __future__ import annotations
from .model import Note, Vault
from .legacy import read_zero, read_one, read_three
from recordkit.validation import mapping, sequence, text, strings, boolean, Invalid

VERSION = 4

class FormatError(ValueError):
    """The input is not a supported vault file."""

def decode(document: object) -> Vault:
    try:
        if isinstance(document, list):
            return read_zero(document)
        document = mapping(document)
        version = document.get("version")
        if version == 1:
            return read_one(document)
        if version == 3:
            return read_three(document)
        if version != VERSION:
            raise FormatError("unsupported vault version")
        notes: list[Note] = []
        for row in sequence(document["notes"]):
            notes.append(Note(text(row["id"]), text(row["title"]), text(row["body"]),
                              strings(row.get("labels", [])),
                              boolean(row.get("pinned", False)),
                              boolean(row.get("archived", False)),
                              row.get("created"), mapping(row.get("extra", {}))))
        return Vault(notes, mapping(document.get("extra", {})))
    except (KeyError, TypeError, Invalid, IndexError) as exc:
        raise FormatError("malformed vault") from exc

def encode(vault: Vault) -> dict[str, object]:
    return {"version": VERSION, "notes": [
        {"id": note.id, "title": note.title, "body": note.body,
         "labels": note.labels, "archived": note.archived,
         "created": note.created, "extra": note.extra} for note in vault.notes],
        "extra": vault.extra}
