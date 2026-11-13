"""Saved searches on disk.

A saved-search file is JSON. Files from before named searches existed
(version 0) are a bare list of search strings; they are upgraded the first
time they are loaded. Version 1 is::

    {"version": 1, "searches": [{"name": "...", "query": "..."}]}

``query`` is the search exactly as ``render`` wrote it.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass

from .nodes import Node
from .parser import parse
from .render import render

FORMAT_VERSION = 1


class StoreError(ValueError):
    """The file is not a saved-search file this version can read."""


@dataclass(frozen=True)
class SavedSearch:
    name: str
    query: str

    @classmethod
    def from_node(cls, name: str, node: Node) -> SavedSearch:
        return cls(name, render(node))

    def node(self) -> Node:
        return parse(self.query)


def load_searches(path: str) -> list[SavedSearch]:
    with open(path, encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise StoreError(f"{path}: not JSON ({exc})") from exc

    if isinstance(data, list):
        searches = [SavedSearch(f"search-{i}", str(query)) for i, query in enumerate(data, start=1)]
        save_searches(path, searches)  # upgrade in place so the next load is quick
        return searches

    if not isinstance(data, dict) or data.get("version") != FORMAT_VERSION:
        raise StoreError(f"{path}: unsupported saved-search format")
    try:
        return [SavedSearch(str(item["name"]), str(item["query"])) for item in data["searches"]]
    except (KeyError, TypeError) as exc:
        raise StoreError(f"{path}: malformed saved search") from exc


def save_searches(path: str, searches: Iterable[SavedSearch]) -> None:
    """Write atomically: a crash mid-save leaves the old file in place."""
    document = {
        "version": FORMAT_VERSION,
        "searches": [{"name": s.name, "query": s.query} for s in searches],
    }
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".findr-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def add_search(path: str, name: str, node: Node) -> None:
    """Append one search to a file, creating the file if needed."""
    searches = load_searches(path) if os.path.exists(path) else []
    searches = [s for s in searches if s.name != name]
    searches.append(SavedSearch.from_node(name, node))
    save_searches(path, searches)
