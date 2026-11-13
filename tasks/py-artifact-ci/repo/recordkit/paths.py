"""Portable relative-path handling for JSON and archive boundaries."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
import re

def relative_name(raw: str) -> str:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise ValueError("expected a nonempty portable relative path")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", raw):
        raise ValueError("path escapes its root")
    result = path.as_posix()
    if result == ".":
        raise ValueError("expected a file path")
    return result

def beneath(root: Path, name: str) -> Path:
    result = root / relative_name(name)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("path resolves outside its root")
    return result

def suffix(name: str) -> str:
    return PurePosixPath(relative_name(name)).suffix.lower()

def parent_names(name: str) -> tuple[str, ...]:
    path = PurePosixPath(relative_name(name))
    return tuple(parent.as_posix() for parent in reversed(path.parents) if parent.as_posix() != ".")

def common_prefix(names: list[str]) -> str:
    if not names:
        return ""
    parts = [PurePosixPath(relative_name(name)).parts for name in names]
    prefix: list[str] = []
    for group in zip(*parts):
        if len(set(group)) != 1:
            break
        prefix.append(group[0])
    return "/".join(prefix)

def replace_suffix(name: str, extension: str) -> str:
    if extension and (not extension.startswith(".") or "/" in extension):
        raise ValueError("extension must start with a dot")
    return PurePosixPath(relative_name(name)).with_suffix(extension).as_posix()
