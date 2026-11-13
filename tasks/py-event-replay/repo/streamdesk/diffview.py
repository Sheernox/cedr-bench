"""Detached before/after reports for operator review of imports and selections."""
from __future__ import annotations
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass

@dataclass(frozen=True)
class Change:
    key: str
    kind: str
    before: dict | None
    after: dict | None
    fields: tuple[str, ...]
    def document(self) -> dict:
        return {"key": self.key, "kind": self.kind, "before": deepcopy(self.before),
                "after": deepcopy(self.after), "fields": list(self.fields)}

def keyed(rows: Iterable[Mapping], key: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        identity = row.get(key)
        if not isinstance(identity, str) or not identity:
            raise ValueError("diff identity must be nonempty text")
        if identity in result:
            raise ValueError("duplicate diff identity: " + identity)
        result[identity] = deepcopy(dict(row))
    return result

def compare(before: Iterable[Mapping], after: Iterable[Mapping], key: str, *, ignore: tuple[str, ...] = ()) -> list[Change]:
    left, right = keyed(before, key), keyed(after, key)
    result = []
    for identity in sorted(left.keys() | right.keys()):
        a, b = left.get(identity), right.get(identity)
        if a is None:
            result.append(Change(identity, "added", None, b, tuple(sorted(b.keys() - set(ignore)))))
        elif b is None:
            result.append(Change(identity, "removed", a, None, tuple(sorted(a.keys() - set(ignore)))))
        else:
            fields = tuple(sorted(k for k in a.keys() | b.keys() if k not in ignore and (k not in a or k not in b or type(a[k]) is not type(b[k]) or a[k] != b[k])))
            if fields:
                result.append(Change(identity, "changed", a, b, fields))
    return result

def counts(changes: Iterable[Change]) -> dict[str, int]:
    result = {"added": 0, "removed": 0, "changed": 0}
    for change in changes:
        result[change.kind] += 1
    return result

def apply(before: Iterable[Mapping], changes: Iterable[Change], key: str) -> list[dict]:
    state = keyed(before, key)
    for change in changes:
        current = state.get(change.key)
        if current != change.before:
            raise ValueError("diff base mismatch: " + change.key)
        if change.after is None:
            state.pop(change.key, None)
        else:
            state[change.key] = deepcopy(change.after)
    return [state[k] for k in sorted(state)]

def reverse(changes: Iterable[Change]) -> list[Change]:
    kinds = {"added": "removed", "removed": "added", "changed": "changed"}
    return [Change(c.key, kinds[c.kind], deepcopy(c.after), deepcopy(c.before), c.fields) for c in reversed(list(changes))]

def text(changes: Iterable[Change]) -> str:
    lines = []
    for change in changes:
        lines.append(f"{change.kind}: {change.key}")
        for field in change.fields:
            a = change.before.get(field) if change.before else None
            b = change.after.get(field) if change.after else None
            lines.append(f"  {field}: {a!r} -> {b!r}")
    return "\n".join(lines) + ("\n" if lines else "")
