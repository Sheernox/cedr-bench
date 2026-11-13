"""Readers for historical releases. Do not write these formats."""
from __future__ import annotations
from datetime import datetime, timezone
from .model import Note, Vault

# v0 had no identity column. The ordinal is stable across loads.
def read_zero(rows: list[dict[str, object]]) -> Vault:
    return Vault([Note(f"legacy-{i}", str(row["title"]), str(row.get("text", "")),
                       pinned=bool(row.get("pinned", False)))
                  for i, row in enumerate(rows, 1)])

def read_one(document: dict[str, object]) -> Vault:
    return Vault([Note(row["id"], row["title"], row["text"],
                       row.get("tags", []), row.get("pinned", False),
                       created=row.get("created")) for row in document["notes"]])

def read_three(document: dict[str, object]) -> Vault:
    return Vault([Note(row["id"], row["title"], row["body"],
                       row.get("labels", []), row.get("pinned", False),
                       created=row.get("created"), extra=row.get("extra", {}))
                  for row in document["notes"]], document.get("extra", {}))
