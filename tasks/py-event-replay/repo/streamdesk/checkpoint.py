"""Atomic file persistence is separate from the in-memory import transaction."""
import json
import os
import tempfile
from pathlib import Path
from .projection import Projection

def load(path: str | Path) -> Projection:
    with open(path, encoding="utf-8") as handle:
        return Projection.restore(json.load(handle))

def save(path: str | Path, projection: Projection) -> None:
    path = Path(path)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".checkpoint-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(projection.snapshot(), handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise
