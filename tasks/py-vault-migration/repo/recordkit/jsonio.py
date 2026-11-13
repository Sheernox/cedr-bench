"""JSON file boundaries with atomic replacement and deterministic encoding."""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

class DocumentError(ValueError):
    """The input is not a complete JSON document."""

def decode(raw: str) -> Any:
    try:
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise DocumentError("invalid JSON document") from exc

def read(path: str | Path) -> Any:
    try:
        return decode(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise DocumentError(f"cannot read {Path(path).name}: {exc.strerror}") from exc

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def atomic_write(path: str | Path, value: Any) -> None:
    path = Path(path)
    raw = canonical(value) + b"\n"
    fd, temporary = tempfile.mkstemp(prefix=".record-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise

def read_lines(path: str | Path) -> Iterable[Any]:
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield decode(line)
            except DocumentError as exc:
                raise DocumentError(f"line {number}: invalid JSON") from exc

def write_lines(path: str | Path, values: Iterable[Any]) -> int:
    count = 0
    with Path(path).open("wb") as handle:
        for value in values:
            handle.write(canonical(value) + b"\n")
            count += 1
    return count

def pretty(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                      allow_nan=False) + "\n"
