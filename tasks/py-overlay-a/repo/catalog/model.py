"""Half-open interval entries on an integer schedule axis."""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Any
from copy import deepcopy
from recordkit.validation import mapping, text, integer, boolean

@dataclass(frozen=True)
class Entry:
    space: str
    start: int
    end: int
    revision: int
    value: dict[str, Any]
    deleted: bool = False

    def __post_init__(self) -> None:
        text(self.space, "space", empty=False)
        integer(self.start, "start")
        integer(self.end, "end")
        integer(self.revision, "revision", minimum=0)
        mapping(self.value, "value")
        boolean(self.deleted, "deleted")
        if self.end <= self.start:
            raise ValueError("interval must have start < end")

    @property
    def identity(self) -> tuple[str, int, int]:
        return self.space, self.start, self.end

    def bounded(self, start: int, end: int) -> Entry:
        return replace(self, start=start, end=end, value=deepcopy(self.value))

    def document(self) -> dict[str, Any]:
        return {"space":self.space, "start":self.start, "end":self.end,
                "revision":self.revision, "value":deepcopy(self.value), "deleted":self.deleted}

def decode(value: object) -> Entry:
    row = mapping(value)
    return Entry(row["space"], row["start"], row["end"], row["revision"],
                 mapping(row.get("value",{})), row.get("deleted",False))
