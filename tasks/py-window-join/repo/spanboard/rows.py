"""Validation and revision normalization shared by importers."""
from .errors import InvalidRow, RevisionConflict
FIELDS = {"id", "revision", "channel", "start", "end", "priority", "value"}

def validate(row: dict) -> dict:
    if not isinstance(row, dict) or not FIELDS <= set(row) or set(row) - FIELDS - {"deleted"}:
        raise InvalidRow("invalid fields")
    if any(not isinstance(row[k], str) or not row[k] for k in ("id", "channel")) or not isinstance(row["value"], str):
        raise InvalidRow("invalid text")
    if any(type(row[k]) is not int for k in ("revision", "start", "end", "priority")) or row["revision"] < 0 or row["start"] >= row["end"]:
        raise InvalidRow("invalid integer range")
    if "deleted" in row and type(row["deleted"]) is not bool:
        raise InvalidRow("invalid deletion marker")
    return {**row, "deleted": row.get("deleted", False)}

def latest(rows) -> list[dict]:
    chosen = {}
    for raw in rows:
        row = validate(raw)
        if row["id"] not in chosen or row["revision"] >= chosen[row["id"]]["revision"]:
            chosen[row["id"]] = row
    return [row for row in chosen.values() if not row["deleted"]]
