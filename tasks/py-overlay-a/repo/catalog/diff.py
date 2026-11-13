"""Human-readable changes between two visible catalog views."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Iterable
from .model import Entry

@dataclass(frozen=True)
class Change:
    identity: tuple[str, int, int]
    kind: str
    before: Entry | None
    after: Entry | None

    def document(self) -> dict[str, object]:
        return {"space": self.identity[0], "start": self.identity[1], "end":self.identity[2], "kind": self.kind,
                "before": self.before.document() if self.before else None,
                "after": self.after.document() if self.after else None}

def compare(before: Iterable[Entry], after: Iterable[Entry]) -> list[Change]:
    left = {entry.identity: entry for entry in before}
    right = {entry.identity: entry for entry in after}
    changes: list[Change] = []
    for identity in sorted(left.keys() | right.keys()):
        old, new = left.get(identity), right.get(identity)
        if old == new:
            continue
        kind = "added" if old is None else "removed" if new is None else "changed"
        changes.append(Change(identity, kind, old, new))
    return changes
