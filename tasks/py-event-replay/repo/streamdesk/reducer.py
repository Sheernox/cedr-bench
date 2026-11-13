"""Apply a validated event to a private account materialization."""
from .errors import InvalidEvent

def reduce_event(accounts: dict, event: dict) -> None:
    key, kind, data = event["account"], event["kind"], event["data"]
    if kind == "open":
        if key in accounts:
            raise InvalidEvent("account already open")
        accounts[key] = {"label": data["label"], "balance": 0, "tags": sorted(set(data.get("tags", [])))}
        return
    if key not in accounts:
        raise InvalidEvent("account is not open")
    row = accounts[key]
    if kind == "credit":
        row["balance"] += data["cents"]
    elif kind == "label":
        row["label"] = data["label"]
    elif kind == "tags":
        row["tags"] = sorted((set(row["tags"]) - set(data["remove"])) | set(data["add"]))
    elif kind == "close":
        del accounts[key]
