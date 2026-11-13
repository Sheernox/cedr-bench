"""Application session binds import, checkpoint and report operations.

The projection owns domain transactions. The session records successful
operator actions only, and keeps its audit log out of domain checkpoints.
"""
from __future__ import annotations
from copy import deepcopy
from .projection import Projection
from .audit import AuditLog
from .diffview import compare
from .views import View, ViewCatalog

class Session:
    def __init__(self, checkpoint: dict | None = None) -> None:
        self.projection = Projection.restore(checkpoint) if checkpoint is not None else Projection()
        self.audit = AuditLog()
        self.views = ViewCatalog()
        self.views.add(View("accounts", sort="account"))

    def import_events(self, events, timestamp: str) -> dict:
        before = self.account_rows()
        accepted = self.projection.apply(events)
        after = self.account_rows()
        changes = compare(before, after, "account")
        self.audit.append("import", {"accepted": accepted, "changed": len(changes)}, timestamp)
        return {"accepted": accepted, "changes": [c.document() for c in changes]}

    def account_rows(self) -> list[dict]:
        return [{"account": key, **deepcopy(value)} for key, value in sorted(self.projection.snapshot()["accounts"].items())]

    def event_rows(self) -> list[dict]:
        return deepcopy(self.projection.snapshot()["events"])

    def source_rows(self) -> list[dict]:
        return [{"source": source, "position": position} for source, position in sorted(self.projection.snapshot()["positions"].items())]

    def report(self, view: str = "accounts", index: int = 0) -> list[dict]:
        return self.views.get(view).apply(self.account_rows(), index)

    def totals(self) -> dict:
        rows = self.account_rows()
        return {"accounts": len(rows), "balance": sum(r["balance"] for r in rows),
                "sources": len(self.source_rows()), "receipts": len(self.event_rows())}

    def document(self) -> dict:
        return {"checkpoint": self.projection.snapshot(), "audit": self.audit.export(), "views": self.views.export()}

    @classmethod
    def restore(cls, document: dict) -> "Session":
        instance = cls(document["checkpoint"])
        instance.audit = AuditLog.restore(document["audit"])
        instance.views = ViewCatalog.restore(document["views"])
        return instance

    def close(self, account: str, event_id: str, source: str, seq: int, timestamp: str) -> dict:
        return self.import_events([{"id": event_id, "source": source, "seq": seq, "account": account, "kind": "close", "data": {}}], timestamp)

    def label(self, account: str, label: str, event_id: str, source: str, seq: int, timestamp: str) -> dict:
        return self.import_events([{"id": event_id, "source": source, "seq": seq, "account": account, "kind": "label", "data": {"label": label}}], timestamp)

    def receipt(self, event_id: str) -> dict | None:
        return next((r for r in self.event_rows() if r["id"] == event_id), None)

    def account(self, account: str) -> dict | None:
        return next((r for r in self.account_rows() if r["account"] == account), None)
