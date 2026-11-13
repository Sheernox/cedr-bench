"""Validation at the import boundary; event dictionaries are the wire format."""
from copy import deepcopy
from .errors import InvalidEvent
FIELDS = {"id", "source", "seq", "account", "kind", "data"}
KINDS = {"open", "credit", "label", "tags", "close"}

def strings(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)

def validate(event: dict) -> dict:
    if not isinstance(event, dict) or not FIELDS <= set(event) or set(event) - FIELDS - {"after"}:
        raise InvalidEvent("expected the six event fields")
    for key in ("id", "source", "account"):
        if not isinstance(event[key], str) or not event[key].strip():
            raise InvalidEvent(f"{key} must be a nonblank string")
    if type(event["seq"]) is not int or event["seq"] <= 0:
        raise InvalidEvent("seq must be a positive integer")
    kind, data = event["kind"], event["data"]
    if not isinstance(kind, str) or kind not in KINDS or not isinstance(data, dict):
        raise InvalidEvent("unsupported event kind or data")
    if kind == "open":
        valid = set(data) in ({"label"}, {"label", "tags"}) and isinstance(data.get("label"), str) and strings(data.get("tags", []))
    elif kind == "credit":
        valid = set(data) == {"cents"} and type(data["cents"]) is int
    elif kind == "label":
        valid = set(data) == {"label"} and isinstance(data["label"], str)
    elif kind == "tags":
        valid = set(data) == {"add", "remove"} and strings(data["add"]) and strings(data["remove"])
    else:
        valid = not data
    if not valid:
        raise InvalidEvent(f"invalid {kind} data")
    after = event.get("after", [])
    if not strings(after) or any(not value.strip() for value in after) or event["id"] in after:
        raise InvalidEvent("invalid dependency IDs")
    return deepcopy({**event, "after": sorted(set(after))})
