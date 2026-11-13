"""Timeline session retains imported revisions and view state independently."""
from __future__ import annotations
from copy import deepcopy
from .rows import validate
from .timeline import build
from .csvview import export_csv
from .audit import AuditLog
from .views import View, ViewCatalog

class Session:
    def __init__(self, rows=None) -> None:
        self._rows = [validate(r) for r in rows] if rows is not None else []
        self.audit = AuditLog()
        self.views = ViewCatalog()
        self.views.add(View("revisions", sort="id"))

    def append(self, rows, timestamp: str) -> int:
        pending = [validate(r) for r in rows]
        # Revision conflicts are checked by materialization, not transport import.
        self._rows.extend(pending)
        self.audit.append("append", {"rows": len(pending)}, timestamp)
        return len(pending)

    def raw_rows(self) -> list[dict]:
        return deepcopy(self._rows)

    def timeline(self, start: int, end: int) -> list[dict]:
        return build(iter(self._rows), start, end)

    def csv(self, start: int, end: int) -> str:
        return export_csv(iter(self._rows), start, end)

    def report(self, view: str = "revisions", page: int = 0) -> list[dict]:
        return self.views.get(view).apply(self.raw_rows(), page)

    def channels(self) -> list[str]:
        return sorted({row["channel"] for row in self._rows})

    def bounds(self) -> tuple[int, int] | None:
        if not self._rows:
            return None
        return min(r["start"] for r in self._rows), max(r["end"] for r in self._rows)

    def totals(self) -> dict:
        return {"rows": len(self._rows), "ids": len({r["id"] for r in self._rows}), "channels": len(self.channels())}

    def document(self) -> dict:
        return {"rows": self.raw_rows(), "audit": self.audit.export(), "views": self.views.export()}

    @classmethod
    def restore(cls, document: dict) -> "Session":
        instance = cls(document["rows"])
        instance.audit = AuditLog.restore(document["audit"])
        instance.views = ViewCatalog.restore(document["views"])
        return instance

    def coverage(self, start: int, end: int) -> list[dict]:
        totals = {}
        for segment in self.timeline(start, end):
            totals[segment["channel"]] = totals.get(segment["channel"], 0) + segment["end"] - segment["start"]
        return [{"channel": key, "ticks": value} for key, value in sorted(totals.items())]

    def values(self, start: int, end: int) -> list[dict]:
        totals = {}
        for segment in self.timeline(start, end):
            key = segment["channel"], segment["value"]
            totals[key] = totals.get(key, 0) + segment["end"] - segment["start"]
        return [{"channel": key[0], "value": key[1], "ticks": value} for key, value in sorted(totals.items())]
