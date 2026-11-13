"""Atomic index persistence. Loading never performs a write."""
from __future__ import annotations
from pathlib import Path
from .state import Catalog
from recordkit.jsonio import read, atomic_write
from recordkit.validation import mapping, sequence

def load(path: Path) -> Catalog:
    if not path.exists():
        return Catalog()
    document = mapping(read(path))
    if document.get("format") != 1:
        raise ValueError("unsupported catalog format")
    return Catalog.restore(sequence(document["entries"]))

def save(path: Path, catalog: Catalog) -> None:
    atomic_write(path, {"format": 1, "entries": catalog.snapshot()})
