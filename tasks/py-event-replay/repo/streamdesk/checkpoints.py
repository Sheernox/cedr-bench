"""Decode checkpoint documents without interpreting transport details."""
from copy import deepcopy
from .errors import InvalidCheckpoint, InvalidEvent
from .events import validate, strings

def decode(document: dict) -> tuple[dict, list[dict], list[dict], dict]:
    try:
        version = document["version"]
        if type(version) is not int or version not in (1, 2, 3):
            raise ValueError("version")
        accounts = deepcopy(document["accounts"])
        if not isinstance(accounts, dict):
            raise ValueError("accounts")
        for key, row in accounts.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(row, dict):
                raise ValueError("account")
            if version == 1:
                row.setdefault("tags", [])
            if set(row) != {"label", "balance", "tags"} or not isinstance(row["label"], str) or type(row["balance"]) is not int or not strings(row["tags"]):
                raise ValueError("account value")
            row["tags"] = sorted(set(row["tags"]))
        if version == 1:
            if type(document["cursor"]) is not int or document["cursor"] < 0:
                raise ValueError("cursor")
            return accounts, [], [], {"*": document["cursor"]}
        events = [validate(x) for x in document["events"]]
        pending = [validate(x) for x in document["pending"]] if version == 3 else []
        positions = document["positions"]
        actual = {}
        ids, pairs = set(), set()
        for event in events + pending:
            pair = event["source"], event["seq"]
            if event["id"] in ids or pair in pairs:
                raise ValueError("duplicate receipt")
            ids.add(event["id"]); pairs.add(pair)
            actual[event["source"]] = max(actual.get(event["source"], 0), event["seq"])
        if not isinstance(positions, dict) or any(type(v) is not int for v in positions.values()) or positions != actual:
            raise ValueError("positions")
        return accounts, events, [], deepcopy(positions)
    except (KeyError, TypeError, ValueError, InvalidEvent) as exc:
        raise InvalidCheckpoint("invalid checkpoint") from exc
