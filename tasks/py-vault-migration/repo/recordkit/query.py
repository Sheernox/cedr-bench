"""Small field filters used by list and export commands, with no eval."""
from __future__ import annotations
import shlex
from dataclasses import dataclass
from collections.abc import Iterable, Mapping

@dataclass(frozen=True)
class Term:
    field: str | None
    value: str
    excluded: bool = False

def parse(raw: str) -> tuple[Term, ...]:
    terms: list[Term] = []
    for token in shlex.split(raw):
        excluded = token.startswith("-")
        if excluded:
            token = token[1:]
        if not token:
            raise ValueError("empty filter term")
        if ":" in token:
            field, value = token.split(":", 1)
            if not field or not value:
                raise ValueError("field filters require a field and value")
            terms.append(Term(field, value, excluded))
        else:
            terms.append(Term(None, token, excluded))
    return tuple(terms)

def _values(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from _values(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _values(child)
    elif value is not None:
        yield str(value)

def matches(row: Mapping[str, object], terms: tuple[Term, ...]) -> bool:
    for term in terms:
        values = _values(row if term.field is None else row.get(term.field))
        found = any(term.value.casefold() in value.casefold() for value in values)
        if found == term.excluded:
            return False
    return True

def select(rows: Iterable[Mapping[str, object]], raw: str) -> list[Mapping[str, object]]:
    terms = parse(raw)
    return [row for row in rows if matches(row, terms)]

def project(row: Mapping[str, object], fields: tuple[str, ...]) -> dict[str, object]:
    return {key: row.get(key) for key in fields}

def order(rows: Iterable[Mapping[str, object]], field: str,
          reverse: bool = False) -> list[Mapping[str, object]]:
    def key(row: Mapping[str, object]) -> tuple[bool, str]:
        value = row.get(field)
        return value is None, str(value).casefold() if value is not None else ""
    return sorted(rows, key=key, reverse=reverse)
