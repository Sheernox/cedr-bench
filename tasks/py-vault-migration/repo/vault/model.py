"""Current in-memory schema, independent of the on-disk revision."""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any
from copy import deepcopy

@dataclass
class Note:
    id: str
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    pinned: bool = False
    archived: bool = False
    created: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def clone(self) -> Note:
        return deepcopy(self)

@dataclass
class Vault:
    notes: list[Note] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def get(self, identity: str) -> Note:
        for note in self.notes:
            if note.id == identity:
                return note.clone()
        raise KeyError(identity)

    def replace(self, note: Note) -> None:
        for index, old in enumerate(self.notes):
            if old.id == note.id:
                self.notes[index] = note.clone()
                return
        self.notes.append(note.clone())

    def remove(self, identity: str) -> None:
        self.notes = [note for note in self.notes if note.id != identity]
