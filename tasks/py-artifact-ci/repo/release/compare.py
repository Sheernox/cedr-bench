"""Review changes between release manifests without unpacking payloads."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Iterable

@dataclass(frozen=True)
class Change:
    name: str
    kind: str
    fields: tuple[str,...] = ()

def compare(before: Iterable[dict[str,object]],after: Iterable[dict[str,object]]) -> list[Change]:
    old={row["name"]:row for row in before}
    new={row["name"]:row for row in after}
    result=[]
    for name in sorted(old.keys()|new.keys()):
        if name not in old:
            result.append(Change(name,"added"))
        elif name not in new:
            result.append(Change(name,"removed"))
        else:
            fields=tuple(key for key in ["size","sha256","executable"] if old[name][key]!=new[name][key])
            if fields:
                result.append(Change(name,"changed",fields))
    return result
