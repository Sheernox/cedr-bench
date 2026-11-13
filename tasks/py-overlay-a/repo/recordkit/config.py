"""Typed TOML settings for optional command-line output preferences."""
from __future__ import annotations
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from collections.abc import Mapping
from .validation import mapping, text, integer, boolean, reject_unknown

@dataclass(frozen=True)
class Preferences:
    format: str = "table"
    page_size: int = 100
    quiet: bool = False
    audit: str | None = None
    columns: tuple[str, ...] = ()

def decode(document: object) -> Preferences:
    row = mapping(document)
    reject_unknown(row,{"format","page_size","quiet","audit","columns"})
    format = text(row.get("format","table"))
    if format not in {"table","json","csv"}:
        raise ValueError("unsupported output format")
    page_size = integer(row.get("page_size",100),minimum=1)
    quiet = boolean(row.get("quiet",False))
    audit = row.get("audit")
    if audit is not None:
        audit = text(audit,empty=False)
    columns = row.get("columns",[])
    if not isinstance(columns,list) or not all(isinstance(value,str) for value in columns):
        raise ValueError("columns must be an array of strings")
    return Preferences(format,page_size,quiet,audit,tuple(columns))

def load(path: Path) -> Preferences:
    try:
        with path.open("rb") as handle:
            document = tomllib.load(handle)
        return decode(document)
    except (OSError,ValueError) as exc:
        raise ValueError(f"cannot read preferences: {path.name}") from exc

def overlay(base: Preferences, values: Mapping[str, object]) -> Preferences:
    document = {"format":base.format,"page_size":base.page_size,"quiet":base.quiet,
                "audit":base.audit,"columns":list(base.columns)}
    document.update(values)
    return decode(document)

def serialize(preferences: Preferences) -> str:
    import json
    lines = [f"format = {json.dumps(preferences.format)}",
             f"page_size = {preferences.page_size}",
             f"quiet = {str(preferences.quiet).lower()}",
             f"columns = {json.dumps(list(preferences.columns))}"]
    if preferences.audit is not None:
        lines.append(f"audit = {json.dumps(preferences.audit)}")
    return "\n".join(lines) + "\n"

def apply_environment(base: Preferences, environ: Mapping[str,str], prefix: str) -> Preferences:
    values: dict[str, object] = {}
    for name in ("format","page_size","quiet","audit"):
        raw = environ.get(prefix + name.upper())
        if raw is None or raw == "":
            continue
        if name == "page_size":
            values[name] = int(raw)
        elif name == "quiet":
            if raw.lower() not in {"true","false","1","0"}:
                raise ValueError("quiet must be true, false, 1 or 0")
            values[name] = raw.lower() in {"true","1"}
        else:
            values[name] = raw
    return overlay(base,values)
