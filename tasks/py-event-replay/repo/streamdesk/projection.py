"""Owns the account projection; adapters share this service for each import."""
from copy import deepcopy
from collections.abc import Iterable
from .events import validate
from .errors import Conflict
from .reducer import reduce_event
from .checkpoints import decode
from .dependencies import partition

class Projection:
    def __init__(self) -> None:
        self.accounts = {}
        self.events = []
        self.positions = {}
        self.pending = []

    def apply(self, events: Iterable[dict]) -> int:
        accounts = dict(self.accounts)
        receipts = list(self.events)
        pending = list(self.pending)
        positions = dict(self.positions)
        known = {e["id"]: e for e in receipts}
        count = 0
        for raw in events:
            event = validate(raw)
            source, seq = event["source"], event["seq"]
            if seq <= max(positions.values(), default=0):
                continue
            if event["id"] in known:
                if known[event["id"]] != event:
                    raise Conflict("event ID reused")
                continue
            known[event["id"]] = event
            pending.append(event)
            positions[source] = seq
            count += 1
        ready, pending = partition(pending, {e["id"] for e in receipts})
        for event in ready:
            reduce_event(accounts, event)
            receipts.append(event)
        self.accounts, self.events, self.pending, self.positions = accounts, receipts, pending, positions
        return count

    def snapshot(self) -> dict:
        return {"version": 3, "accounts": self.accounts, "events": self.events, "pending": self.pending, "positions": self.positions}

    @classmethod
    def restore(cls, document: dict) -> "Projection":
        instance = cls()
        instance.accounts, instance.events, instance.pending, instance.positions = decode(document)
        return instance
