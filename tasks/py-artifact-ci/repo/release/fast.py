"""Low-allocation path-only inventory for CI planning."""
from __future__ import annotations
import os
from pathlib import Path
from .rules import Policy

def inventory(root: Path, policy: Policy) -> list[str]:
    result=[]
    for directory, dirs, names in os.walk(root):
        base=Path(directory)
        dirs[:]=[name for name in sorted(dirs)
                 if policy.included((base/name).relative_to(root).as_posix(),True)]
        for name in sorted(names):
            path=base/name
            rel=path.relative_to(root).as_posix()
            if policy.included(rel):
                result.append(rel)
    return sorted(result)
