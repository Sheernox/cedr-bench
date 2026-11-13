"""Command dispatch is shared by the CLI and embedding operator consoles.

Commands operate on session methods. Domain exceptions intentionally propagate
so callers can choose a transport status without hiding the actionable cause.
"""
from __future__ import annotations
from collections.abc import Callable
from .cursors import ReportSnapshot, query_identity
from .query import select
from .table import Column, plain, html

class CommandError(ValueError):
    """An operator command is unsupported or malformed."""

class Commands:
    def __init__(self, session) -> None:
        self.session = session
        self._commands: dict[str, Callable] = {
            "totals": self.totals,
            "views": self.views,
            "report": self.report,
            "audit": self.audit,
            "snapshot": self.snapshot,
            "report-page": self.report_page,
        }

    def execute(self, name: str, arguments: dict) -> object:
        if not isinstance(arguments, dict):
            raise CommandError("command arguments must be an object")
        if name not in self._commands:
            raise CommandError("unknown command: " + name)
        return self._commands[name](arguments)

    def names(self) -> list[str]:
        return sorted(self._commands)

    def totals(self, arguments: dict) -> dict:
        if arguments:
            raise CommandError("totals takes no arguments")
        return self.session.totals()

    def views(self, arguments: dict) -> list[dict]:
        if arguments:
            raise CommandError("views takes no arguments")
        return self.session.views.export()

    def report(self, arguments: dict) -> list[dict]:
        if set(arguments) - {"view", "page", "filter"}:
            raise CommandError("unknown report argument")
        view = arguments.get("view")
        page = arguments.get("page", 0)
        if view is None:
            names = self.session.views.export()
            if not names:
                return []
            view = names[0]["name"]
        if not isinstance(view, str):
            raise CommandError("view must be a name")
        result = self.session.report(view, page)
        return select(result, arguments.get("filter", {}))

    def audit(self, arguments: dict) -> list[dict]:
        if set(arguments) - {"action"}:
            raise CommandError("unknown audit argument")
        action = arguments.get("action")
        if action is None:
            return self.session.audit.export()
        if not isinstance(action, str):
            raise CommandError("action must be text")
        return self.session.audit.actions(action)

    def snapshot(self, arguments: dict) -> dict:
        if arguments:
            raise CommandError("snapshot takes no arguments")
        return self.session.document()

    def format_report(self, arguments: dict, columns: tuple[Column, ...], format: str = "text") -> str:
        rows = self.report(arguments)
        if format == "text":
            return plain(rows, columns)
        if format == "html":
            return html(rows, columns, "Report")
        raise CommandError("format must be text or html")

    def report_page(self, arguments: dict) -> dict:
        options = {key: value for key, value in arguments.items() if key != "cursor"}
        rows = self.report(options)
        snapshot = ReportSnapshot(rows, query_identity(options, ()))
        token = arguments.get("cursor")
        return snapshot.first() if token is None else snapshot.resume(token)
