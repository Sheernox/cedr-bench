"""The parsed form of a search.

Nodes are immutable and compare by value, so two searches that mean the same
thing parse to equal trees. ``And`` and ``Or`` always hold at least two items.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    """``value`` anywhere (field is None) or ``field:value``."""

    field: str | None
    value: str


@dataclass(frozen=True)
class Compare:
    """``field>number`` and friends. ``number`` keeps the text the user typed."""

    field: str
    op: str
    number: str


@dataclass(frozen=True)
class Not:
    item: Node


@dataclass(frozen=True)
class And:
    items: tuple[Node, ...]


@dataclass(frozen=True)
class Or:
    items: tuple[Node, ...]


Node = Term | Compare | Not | And | Or
