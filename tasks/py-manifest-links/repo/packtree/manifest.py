"""Structural validation builds a detached lookup for virtual resolution."""
from copy import deepcopy
from .errors import ManifestError
from .lexical import canonical

def index(manifest: dict) -> dict[str, dict]:
    if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("entries"), list):
        raise ManifestError("expected manifest version 1")
    entries = {"": {"path": "", "kind": "dir"}}
    for row in manifest["entries"]:
        if not isinstance(row, dict) or not canonical(row.get("path", "")):
            raise ManifestError("noncanonical entry")
        kind = row.get("kind")
        fields = {"path", "kind"} | ({"text"} if kind == "file" else {"target"} if kind == "link" else {"source"} if kind == "mount" else set())
        if kind not in ("dir", "file", "link", "mount") or set(row) != fields:
            raise ManifestError("invalid entry kind or fields")
        if kind == "file" and not isinstance(row["text"], str) or kind == "link" and not isinstance(row["target"], str):
            raise ManifestError("expected string payload")
        if kind == "mount" and (not isinstance(row["source"], str) or not row["source"].strip()):
            raise ManifestError("mount source required")
        if row["path"] in entries:
            raise ManifestError("duplicate entry")
        entries[row["path"]] = deepcopy(row)
    for path in entries:
        if not path:
            continue
        parent = path.rpartition("/")[0]
        if parent not in entries or entries[parent]["kind"] != "dir":
            raise ManifestError("entry parent must be a directory")
    return entries
