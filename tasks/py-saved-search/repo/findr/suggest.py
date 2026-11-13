"""Build searches from records, for the app's "find similar" button."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

DEFAULT_FIELDS = ("project", "owner", "status", "path")


def similar_to(record: Mapping[str, object], fields: Iterable[str] = DEFAULT_FIELDS) -> str:
    """A search for records that share the given fields with ``record``.

    Fields the record lacks, or holds no value for, are left out. Values are
    always quoted so that any text is safe.
    """
    parts = []
    for field in fields:
        value = record.get(field)
        if value is None or value == "":
            continue
        text = str(value).replace('"', '\\"')
        parts.append(f'{field}:"{text}"')
    return " ".join(parts)
