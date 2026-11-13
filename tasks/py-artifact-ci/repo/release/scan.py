"""Build-time inventory, retaining portable paths and file modes."""
from __future__ import annotations
import os
from pathlib import Path
from collections.abc import Iterator
from dataclasses import dataclass
from .rules import Policy
from recordkit.paths import relative_name

@dataclass(frozen=True)
class File:
    name: str
    source: Path
    executable: bool

    def read(self) -> bytes:
        return self.source.read_bytes()

def walk(root: Path, policy: Policy) -> Iterator[File]:
    def visit(directory: Path) -> Iterator[File]:
        for path in sorted(directory.iterdir()):
            name = relative_name(path.relative_to(root).as_posix())
            if path.is_dir():
                if policy.included(name,True):
                    yield from visit(path)
            elif path.is_file() and policy.included(name):
                yield File(name,path,bool(path.stat().st_mode & 0o111))
    yield from visit(root)
