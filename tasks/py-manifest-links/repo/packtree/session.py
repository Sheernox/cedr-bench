"""Package session coordinates navigation, selection and detached reports."""
from __future__ import annotations
from copy import deepcopy
from .manifest import index
from .api import preview
from .resolve import resolve
from .export import export
from .audit import AuditLog
from .views import ViewCatalog, View, Navigation
from .diffview import compare

class Session:
    def __init__(self, manifest: dict) -> None:
        index(manifest)
        self._manifest = deepcopy(manifest)
        self.audit = AuditLog()
        self.views = ViewCatalog()
        self.views.add(View("entries", sort="path"))
        self.navigation = Navigation()
        self._selection: list[dict] = []

    def browse(self, path: str) -> dict:
        result = preview(self._manifest, path)
        self.navigation.visit(path)
        return result

    def entry_rows(self) -> list[dict]:
        return [deepcopy(r) for _, r in sorted(index(self._manifest).items())]

    def report(self, view: str = "entries", page: int = 0) -> list[dict]:
        return self.views.get(view).apply(self.entry_rows(), page)

    def select(self, path: str, output: str) -> None:
        # Resolve now so an invalid selection does not enter the export queue.
        resolve(self._manifest, path)
        export(self._manifest, [{"path": path, "as": output}])
        self._selection.append({"path": path, "as": output})

    def selections(self) -> list[dict]:
        return deepcopy(self._selection)

    def clear(self) -> None:
        self._selection.clear()

    def remove_selection(self, index: int) -> None:
        if type(index) is not int or not 0 <= index < len(self._selection):
            raise ValueError("selection index out of range")
        del self._selection[index]

    def export(self, timestamp: str) -> list[dict]:
        result = export(self._manifest, self._selection)
        self.audit.append("export", {"selections": len(self._selection), "files": len(result)}, timestamp)
        return result

    def replace(self, manifest: dict, timestamp: str) -> list[dict]:
        new = index(manifest)
        changes = self._entry_changes(new)
        self._manifest = deepcopy(manifest)
        self._selection.clear()
        self.audit.append("replace", {"entries": len(new) - 1}, timestamp)
        return changes

    def _entry_changes(self, new: dict) -> list[dict]:
        before = [r for r in self.entry_rows() if r["path"]]
        after = [r for r in new.values() if r["path"]]
        return [c.document() for c in compare(before, after, "path")]

    def totals(self) -> dict:
        rows = self.entry_rows()
        return {kind: sum(r["kind"] == kind for r in rows if r["path"]) for kind in ("dir", "file", "link")}

    def document(self) -> dict:
        return {"manifest": deepcopy(self._manifest), "selections": self.selections(), "audit": self.audit.export(), "views": self.views.export()}
