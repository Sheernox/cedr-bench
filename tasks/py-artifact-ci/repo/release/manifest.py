"""Bundle manifests are projections of the selected file inventory."""
from __future__ import annotations
import hashlib
from collections.abc import Iterable
from .scan import File
from recordkit.archive import Member
from recordkit.stats import Moments

def members(files: Iterable[File]) -> list[Member]:
    return [Member(file.name,file.read(),file.executable) for file in files]

def describe(rows: Iterable[Member]) -> list[dict[str,object]]:
    return [row.descriptor() for row in sorted(rows,key=lambda row:row.name)]

def summary(rows: list[Member]) -> dict[str,object]:
    sizes=Moments()
    for row in rows:
        sizes.add(len(row.data))
    return {"files":len(rows),"bytes":sum(len(row.data) for row in rows),
            "executables":sum(row.executable for row in rows),"sizes":sizes.document()}
