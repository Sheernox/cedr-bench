"""Validation at JSON and command-line boundaries."""
from __future__ import annotations
from collections.abc import Mapping, Sequence
from typing import Any

class Invalid(ValueError):
    """A value cannot be decoded without losing information."""
    def __init__(self, path: str, expected: str) -> None:
        super().__init__(f"{path}: expected {expected}")
        self.path = path

def mapping(value: Any, path: str = "$") -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise Invalid(path, "object with string keys")
    return value

def sequence(value: Any, path: str = "$") -> list[Any]:
    if not isinstance(value, list):
        raise Invalid(path, "array")
    return value

def text(value: Any, path: str = "$", *, empty: bool = True) -> str:
    if not isinstance(value, str) or (not empty and not value):
        raise Invalid(path, "string" if empty else "nonempty string")
    return value

def integer(value: Any, path: str = "$", *, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise Invalid(path, f"integer >= {minimum}" if minimum is not None else "integer")
    return value

def boolean(value: Any, path: str = "$") -> bool:
    if type(value) is not bool:
        raise Invalid(path, "boolean")
    return value

def strings(value: Any, path: str = "$") -> list[str]:
    return [text(item, f"{path}[{i}]") for i, item in enumerate(sequence(value, path))]

def required(data: Mapping[str, Any], key: str, path: str = "$") -> Any:
    if key not in data:
        raise Invalid(f"{path}.{key}", "present field")
    return data[key]

def choice(value: Any, choices: Sequence[str], path: str = "$") -> str:
    value = text(value, path)
    if value not in choices:
        raise Invalid(path, "one of " + ", ".join(choices))
    return value

def unique(values: Sequence[str], path: str = "$") -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            raise Invalid(path, "unique entries")
        seen.add(value)
        result.append(value)
    return tuple(result)

def optional_text(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    return None if value is None else text(value, key)

def reject_unknown(data: Mapping[str, Any], allowed: set[str], path: str = "$") -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise Invalid(path, "known keys, got " + ", ".join(unknown))
