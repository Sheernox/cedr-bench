"""Transport-neutral JSON, JSONL and CSV readers for offline application adapters.

Readers consume streams rather than opening paths. Resource ownership stays
with the CLI or embedding application. Errors include line numbers, never
entire input records, because account and package data can be sensitive.
"""
from __future__ import annotations
import csv
import io
import json
from collections.abc import Iterable, Iterator, Mapping
from typing import TextIO

class WireError(ValueError):
    """Malformed transport data with an actionable location."""
    def __init__(self, message: str, line: int | None = None) -> None:
        self.line = line
        super().__init__(f"line {line}: {message}" if line is not None else message)

def read_document(stream: TextIO) -> dict:
    try:
        result = json.load(stream)
    except json.JSONDecodeError as exc:
        raise WireError("invalid JSON document", exc.lineno) from exc
    if not isinstance(result, dict):
        raise WireError("expected an object")
    return result

def write_document(stream: TextIO, document: Mapping) -> None:
    json.dump(dict(document), stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write("\n")

def read_lines(stream: TextIO, *, allow_blank: bool = True) -> Iterator[dict]:
    for number, line in enumerate(stream, 1):
        if not line.strip() and allow_blank:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WireError("invalid JSON record", number) from exc
        if not isinstance(row, dict):
            raise WireError("expected a record object", number)
        yield row

def write_lines(stream: TextIO, rows: Iterable[Mapping]) -> int:
    count = 0
    for row in rows:
        stream.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
        count += 1
    return count

def read_csv(stream: TextIO, columns: tuple[str, ...]) -> Iterator[dict[str, str]]:
    reader = csv.DictReader(stream)
    if reader.fieldnames != list(columns):
        raise WireError("expected CSV columns: " + ", ".join(columns), 1)
    try:
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise WireError("wrong number of CSV fields", reader.line_num)
            yield row
    except csv.Error as exc:
        raise WireError("invalid CSV quoting", reader.line_num) from exc

def write_csv(stream: TextIO, rows: Iterable[Mapping], columns: tuple[str, ...]) -> int:
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    count = 0
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in columns})
        count += 1
    return count

def require_text(value: object, field: str, *, empty: bool = True) -> str:
    if not isinstance(value, str) or not empty and not value:
        raise WireError(f"{field} must be text")
    return value

def require_integer(value: object, field: str, *, minimum: int | None = None) -> int:
    if type(value) is not int or minimum is not None and value < minimum:
        raise WireError(f"{field} must be an integer" + (f" >= {minimum}" if minimum is not None else ""))
    return value

def require_fields(row: Mapping, required: set[str], optional: set[str] | None = None) -> None:
    missing = required - row.keys()
    unknown = row.keys() - required - (optional or set())
    if missing:
        raise WireError("missing fields: " + ", ".join(sorted(missing)))
    if unknown:
        raise WireError("unknown fields: " + ", ".join(sorted(unknown)))

def document_text(document: Mapping) -> str:
    stream = io.StringIO()
    write_document(stream, document)
    return stream.getvalue()
