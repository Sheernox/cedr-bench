"""Opaque pagination cursors for detached reports.

These cursors provide query consistency and typo detection, not authorization.
No cursor contains domain rows or sensitive field values. The application must
still check access before selecting a report's input rows.
"""
from __future__ import annotations
import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from copy import deepcopy

class CursorError(ValueError):
    """A report cursor is corrupt or belongs to another query."""

@dataclass(frozen=True)
class Cursor:
    offset: int
    limit: int
    query: str
    snapshot: str

    def __post_init__(self) -> None:
        if type(self.offset) is not int or self.offset < 0:
            raise CursorError("invalid cursor offset")
        if type(self.limit) is not int or not 1 <= self.limit <= 1000:
            raise CursorError("invalid cursor limit")
        if not isinstance(self.query, str) or not isinstance(self.snapshot, str):
            raise CursorError("invalid cursor identity")

    def encode(self) -> str:
        document = {"version": 1, "offset": self.offset, "limit": self.limit,
                    "query": self.query, "snapshot": self.snapshot}
        payload = canonical(document)
        envelope = payload + b"." + hashlib.sha256(payload).hexdigest().encode("ascii")
        return base64.urlsafe_b64encode(envelope).decode("ascii").rstrip("=")

    @classmethod
    def decode(cls, token: str, query: str, snapshot: str) -> "Cursor":
        if not isinstance(token, str) or not 1 <= len(token) <= 8192:
            raise CursorError("invalid cursor token")
        try:
            raw = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
            payload, separator, checksum = raw.rpartition(b".")
            if not separator or hashlib.sha256(payload).hexdigest().encode("ascii") != checksum:
                raise CursorError("cursor checksum mismatch")
            document = json.loads(payload)
            if not isinstance(document, dict) or set(document) != {"version", "offset", "limit", "query", "snapshot"}:
                raise CursorError("invalid cursor fields")
            if type(document.pop("version")) is not int or json.loads(payload)["version"] != 1:
                raise CursorError("unsupported cursor version")
            result = cls(**document)
        except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
            raise CursorError("invalid cursor encoding") from exc
        if result.query != query or result.snapshot != snapshot:
            raise CursorError("cursor belongs to another query or snapshot")
        return result

    def advance(self, count: int) -> "Cursor":
        if type(count) is not int or count < 0:
            raise CursorError("invalid advance count")
        return Cursor(self.offset + count, self.limit, self.query, self.snapshot)

    def previous(self) -> "Cursor":
        return Cursor(max(0, self.offset - self.limit), self.limit, self.query, self.snapshot)


def canonical(document: object) -> bytes:
    return json.dumps(document, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def identity(document: object) -> str:
    return hashlib.sha256(canonical(document)).hexdigest()


def query_identity(view: dict, fields: tuple[str, ...]) -> str:
    return identity({"view": view, "fields": list(fields)})


class ReportSnapshot:
    def __init__(self, rows: Iterable[Mapping], query: str) -> None:
        self._rows = [deepcopy(dict(row)) for row in rows]
        self.query = query
        self.identity = identity(self._rows)

    def first(self, limit: int = 50) -> dict:
        return self.page(Cursor(0, limit, self.query, self.identity))

    def resume(self, token: str) -> dict:
        return self.page(Cursor.decode(token, self.query, self.identity))

    def page(self, cursor: Cursor) -> dict:
        if cursor.query != self.query or cursor.snapshot != self.identity:
            raise CursorError("cursor does not match report")
        start = cursor.offset
        stop = start + cursor.limit
        rows = deepcopy(self._rows[start:stop])
        next_token = cursor.advance(len(rows)).encode() if stop < len(self._rows) else None
        previous_token = cursor.previous().encode() if start else None
        return {"rows": rows, "offset": start, "total": len(self._rows),
                "next": next_token, "previous": previous_token}

    def all(self) -> list[dict]:
        return deepcopy(self._rows)

    def __len__(self) -> int:
        return len(self._rows)


def collect(snapshot: ReportSnapshot, limit: int = 50) -> list[dict]:
    result = []
    current = snapshot.first(limit)
    while True:
        result.extend(current["rows"])
        if current["next"] is None:
            return result
        current = snapshot.resume(current["next"])
