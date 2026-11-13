"""Append-only, hash-linked audit entries for local exports."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from .jsonio import canonical, decode, fingerprint

@dataclass(frozen=True)
class Entry:
    sequence: int
    action: str
    at: str
    payload: dict[str, Any]
    previous: str

    def document(self) -> dict[str, Any]:
        return {"sequence": self.sequence, "action": self.action, "at": self.at,
                "payload": self.payload, "previous": self.previous}

    def digest(self) -> str:
        return fingerprint(self.document())

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def verify(entries: Iterable[Entry]) -> str:
    previous = ""
    for number, entry in enumerate(entries, 1):
        if entry.sequence != number or entry.previous != previous:
            raise ValueError(f"broken audit chain at entry {number}")
        previous = entry.digest()
    return previous

def load(path: Path) -> list[Entry]:
    if not path.exists():
        return []
    entries: list[Entry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = decode(line)
        entries.append(Entry(row["sequence"], row["action"], row["at"],
                             row["payload"], row["previous"]))
    verify(entries)
    return entries

def append(path: Path, action: str, payload: dict[str, Any], at: str | None = None) -> Entry:
    entries = load(path)
    previous = verify(entries)
    entry = Entry(len(entries) + 1, action, at or now(), payload, previous)
    with path.open("ab") as handle:
        handle.write(canonical(entry.document()) + b"\n")
    return entry

def summarize(entries: Iterable[Entry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.action] = counts.get(entry.action, 0) + 1
    return counts
