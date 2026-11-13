"""Reproducible offline release creation."""
from __future__ import annotations
from pathlib import Path
from .rules import Policy
from .scan import walk
from .manifest import members,describe,summary
from recordkit.archive import pack
from recordkit.jsonio import atomic_write

def build(root: Path, lines: list[str], destination: Path) -> list[dict[str,object]]:
    rows=members(walk(root,Policy(lines)))
    raw=pack(rows)
    destination.write_bytes(raw)
    return describe(rows)

def dry_run(root: Path, lines: list[str]) -> dict[str,object]:
    rows=members(walk(root,Policy(lines)))
    return {"manifest":describe(rows),"summary":summary(rows)}
