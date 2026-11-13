"""Terminal tables and delimited exports for offline review."""
from __future__ import annotations
import csv
import io
from dataclasses import dataclass
from collections.abc import Iterable, Mapping, Sequence

@dataclass(frozen=True)
class Column:
    key: str
    label: str
    width: int = 40
    align: str = "left"

def plain(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(plain(item) for item in value)
    return str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ")

def clip(value: str, width: int) -> str:
    if width < 1:
        raise ValueError("column width must be positive")
    return value if len(value) <= width else value[:width - 1] + "~"

def render(rows: Iterable[Mapping[str, object]], columns: Sequence[Column]) -> str:
    cells = [[plain(row.get(col.key)) for col in columns] for row in rows]
    widths = [min(col.width, max([len(col.label), *(len(row[i]) for row in cells)]))
              for i, col in enumerate(columns)]
    def line(values: Sequence[str]) -> str:
        fields: list[str] = []
        for value, col, width in zip(values, columns, widths):
            value = clip(value, width)
            fields.append(value.rjust(width) if col.align == "right" else value.ljust(width))
        return "  ".join(fields).rstrip()
    output = [line([col.label for col in columns])]
    output.extend(line(row) for row in cells)
    return "\n".join(output) + "\n"

def delimited(rows: Iterable[Mapping[str, object]], columns: Sequence[Column],
              delimiter: str = ",") -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
    writer.writerow([column.label for column in columns])
    for row in rows:
        writer.writerow([plain(row.get(column.key)) for column in columns])
    return stream.getvalue()

def parse_delimited(raw: str, keys: Sequence[str], delimiter: str = ",") -> list[dict[str, str]]:
    reader = csv.reader(io.StringIO(raw), delimiter=delimiter)
    next(reader, None)
    rows: list[dict[str, str]] = []
    for number, row in enumerate(reader, 2):
        if len(row) != len(keys):
            raise ValueError(f"row {number}: expected {len(keys)} columns")
        rows.append(dict(zip(keys, row)))
    return rows

def histogram(values: Iterable[str]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))
