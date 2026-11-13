"""Non-lossy JSON export and deliberately human-oriented text views."""
from __future__ import annotations
from .model import Vault
from .codec import encode
from .search import documents
from recordkit.table import Column, render, delimited
from recordkit.jsonio import pretty

COLUMNS = (Column("id", "ID"), Column("title", "TITLE", 50), Column("labels", "LABELS"),
           Column("pinned", "PINNED", 8), Column("archived", "ARCHIVED", 8))

def export(vault: Vault, format: str = "json") -> str:
    if format == "json":
        return pretty(encode(vault))
    if format == "csv":
        return delimited(documents(vault), COLUMNS)
    if format == "table":
        return render(documents(vault), COLUMNS)
    if format == "markdown":
        return "\n\n".join(f"# {note.title}\n\n{note.body}" for note in vault.notes) + "\n"
    raise ValueError("format must be json, csv, table or markdown")
