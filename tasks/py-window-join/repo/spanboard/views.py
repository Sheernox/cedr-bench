"""Saved view configuration and navigation state for terminal report clients."""
from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from .query import compile_filter, select
from .table import ordered, page

@dataclass(frozen=True)
class View:
    name: str
    filter: dict = field(default_factory=dict)
    sort: str = ""
    descending: bool = False
    page_size: int = 50
    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("view name required")
        compile_filter(self.filter)
        if not isinstance(self.sort, str) or type(self.descending) is not bool:
            raise ValueError("invalid sort")
        if type(self.page_size) is not int or not 1 <= self.page_size <= 1000:
            raise ValueError("page_size must be 1-1000")
    def document(self) -> dict:
        return {"name": self.name, "filter": deepcopy(self.filter), "sort": self.sort,
                "descending": self.descending, "page_size": self.page_size}
    @classmethod
    def restore(cls, document: dict) -> "View":
        if not isinstance(document, dict) or set(document) != {"name", "filter", "sort", "descending", "page_size"}:
            raise ValueError("invalid view")
        return cls(**deepcopy(document))
    def apply(self, rows, index: int = 0) -> list[dict]:
        if type(index) is not int or index < 0:
            raise ValueError("page index must be nonnegative")
        chosen = select(rows, self.filter)
        if self.sort:
            chosen = ordered(chosen, self.sort, descending=self.descending)
        return page(chosen, index * self.page_size, self.page_size)

class ViewCatalog:
    def __init__(self) -> None:
        self._views: dict[str, dict] = {}
    def add(self, view: View, *, replace: bool = False) -> None:
        if view.name in self._views and not replace:
            raise ValueError("duplicate view name")
        self._views[view.name] = view.document()
    def get(self, name: str) -> View:
        try:
            return View.restore(self._views[name])
        except KeyError as exc:
            raise ValueError("unknown view: " + name) from exc
    def remove(self, name: str) -> None:
        if name not in self._views:
            raise ValueError("unknown view: " + name)
        del self._views[name]
    def export(self) -> list[dict]:
        return [deepcopy(self._views[name]) for name in sorted(self._views)]
    @classmethod
    def restore(cls, documents: list[dict]) -> "ViewCatalog":
        instance = cls()
        for doc in documents:
            instance.add(View.restore(doc))
        return instance

class Navigation:
    def __init__(self) -> None:
        self._back: list[str] = []
        self._forward: list[str] = []
        self.current = ""
    def visit(self, target: str) -> None:
        if target != self.current:
            self._back.append(self.current)
            self.current = target
            self._forward.clear()
    def back(self) -> str:
        if self._back:
            self._forward.append(self.current)
            self.current = self._back.pop()
        return self.current
    def forward(self) -> str:
        if self._forward:
            self._back.append(self.current)
            self.current = self._forward.pop()
        return self.current
