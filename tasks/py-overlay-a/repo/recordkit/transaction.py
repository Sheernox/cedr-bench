"""Optimistic single-document transactions for offline editing commands."""
from __future__ import annotations
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator
import hashlib
from .jsonio import read, atomic_write

class Conflict(RuntimeError):
    """Another process saved after this editor loaded its copy."""

def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

@dataclass
class Edit:
    path: Path
    original: str | None
    value: Any
    committed: bool = False

    def commit(self, validate: Callable[[Any],None] | None = None) -> None:
        if self.committed:
            raise RuntimeError("transaction already committed")
        if validate is not None:
            validate(self.value)
        if digest(self.path) != self.original:
            raise Conflict("document changed while it was being edited; reload and retry")
        atomic_write(self.path,self.value)
        self.committed = True

def begin(path: Path, default: Any = None) -> Edit:
    before = digest(path)
    value = read(path) if before is not None else deepcopy(default)
    if digest(path) != before:
        raise Conflict("document changed while it was being read; retry")
    return Edit(path,before,value)

@contextmanager
def editing(path: Path, default: Any = None,
            validate: Callable[[Any],None] | None = None) -> Iterator[Edit]:
    edit = begin(path,default)
    yield edit
    if not edit.committed:
        edit.commit(validate)

def backup(path: Path, destination: Path) -> str:
    if destination.exists():
        raise FileExistsError("backup destination already exists")
    raw = path.read_bytes()
    with destination.open("xb") as handle:
        handle.write(raw)
    return hashlib.sha256(raw).hexdigest()

def restore(source: Path, destination: Path, expected_digest: str) -> None:
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_digest:
        raise ValueError("backup integrity check failed")
    from .jsonio import decode
    atomic_write(destination,decode(raw.decode("utf-8")))

def revisions(paths: list[Path]) -> dict[str,str | None]:
    return {str(path):digest(path) for path in paths}
