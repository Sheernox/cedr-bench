"""Content-addressed audit receipts for operator exports.

The chain detects accidental truncation or edits; it is not an authentication
scheme. Applications that need signatures must supply them outside this module.
"""
from __future__ import annotations
from collections.abc import Iterable
from copy import deepcopy
import hashlib
import json

class AuditError(ValueError):
    """An audit export is malformed or inconsistent."""

def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

class AuditLog:
    def __init__(self) -> None:
        self._rows: list[dict] = []

    def append(self, action: str, metadata: dict, timestamp: str) -> dict:
        if not isinstance(action, str) or not action or not isinstance(metadata, dict):
            raise AuditError("action and metadata required")
        from datetime import datetime
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise AuditError("timestamp must be ISO-8601") from exc
        if parsed.utcoffset() is None:
            raise AuditError("timestamp needs an offset")
        row = {"index": len(self._rows), "action": action, "metadata": deepcopy(metadata), "timestamp": timestamp,
               "previous": self._rows[-1]["digest"] if self._rows else ""}
        row["digest"] = digest(row)
        self._rows.append(row)
        return deepcopy(row)

    def export(self) -> list[dict]:
        return deepcopy(self._rows)

    @classmethod
    def restore(cls, rows: Iterable[dict]) -> "AuditLog":
        instance = cls()
        for index, raw in enumerate(rows):
            if not isinstance(raw, dict) or set(raw) != {"index", "action", "metadata", "timestamp", "previous", "digest"}:
                raise AuditError("invalid receipt fields")
            row = deepcopy(raw)
            checksum = row.pop("digest")
            expected_previous = instance._rows[-1]["digest"] if instance._rows else ""
            if type(row["index"]) is not int or row["index"] != index or row["previous"] != expected_previous or checksum != digest(row):
                raise AuditError("invalid receipt chain")
            generated = instance.append(row["action"], row["metadata"], row["timestamp"])
            if generated["digest"] != checksum:
                raise AuditError("receipt mismatch")
        return instance

    def actions(self, action: str) -> list[dict]:
        return [deepcopy(row) for row in self._rows if row["action"] == action]

    def truncate(self, length: int) -> None:
        if type(length) is not int or length < 0 or length > len(self._rows):
            raise AuditError("invalid audit length")
        del self._rows[length:]

    def __len__(self) -> int:
        return len(self._rows)

def compare(left: Iterable[dict], right: Iterable[dict]) -> dict:
    a, b = AuditLog.restore(left).export(), AuditLog.restore(right).export()
    common = 0
    for x, y in zip(a, b):
        if x["digest"] != y["digest"]:
            break
        common += 1
    return {"common": common, "left_only": len(a) - common, "right_only": len(b) - common}
