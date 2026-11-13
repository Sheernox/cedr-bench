"""JSONL page framing; page boundaries are not semantic boundaries."""
from __future__ import annotations
from collections.abc import Iterable, Iterator
from pathlib import Path
from .model import Entry, decode
from recordkit.jsonio import read_lines, write_lines

def read_page(path: str | Path) -> Iterator[Entry]:
    for row in read_lines(path):
        yield decode(row)

def read_pages(paths: Iterable[str | Path]) -> Iterator[Entry]:
    for path in paths:
        yield from read_page(path)

def write_page(path: str | Path, entries: Iterable[Entry]) -> int:
    return write_lines(path, (entry.document() for entry in entries))

def batches(entries: Iterable[Entry], size: int) -> Iterator[list[Entry]]:
    if size <= 0:
        raise ValueError("page size must be positive")
    page: list[Entry] = []
    for entry in entries:
        page.append(entry)
        if len(page) == size:
            yield page
            page = []
    if page:
        yield page
