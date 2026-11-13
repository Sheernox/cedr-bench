"""Turn nodes back into search text.

``parse(render(node)) == node`` for every node ``parse`` can produce: this is
what lets the app save a search as text and load it later.
"""

from __future__ import annotations

from .lexer import KEYWORDS, SPECIAL
from .nodes import And, Compare, Node, Not, Or, Term


def render(node: Node) -> str:
    if isinstance(node, Term):
        value = quote_value(node.value)
        return value if node.field is None else f"{node.field}:{value}"
    if isinstance(node, Compare):
        return f"{node.field}{node.op}{node.number}"
    if isinstance(node, Not):
        return "-" + _atom(node.item)
    if isinstance(node, And):
        return " ".join(_atom(item) for item in node.items)
    if isinstance(node, Or):
        return " OR ".join(f"({render(item)})" if isinstance(item, Or) else render(item) for item in node.items)
    raise TypeError(f"not a search node: {node!r}")


def _atom(node: Node) -> str:
    """Render a node where only a single term fits without parentheses."""
    if isinstance(node, (And, Or)):
        return f"({render(node)})"
    return render(node)


def quote_value(value: str) -> str:
    """The value as typed in a search: bare when that is safe, else quoted."""
    if not _needs_quotes(value):
        return value
    return '"' + value.replace('"', '\\"') + '"'


def _needs_quotes(value: str) -> bool:
    if value == "" or value in KEYWORDS:
        return True
    return any(ch.isspace() or ch in SPECIAL for ch in value)
