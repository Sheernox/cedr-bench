"""Turn pending items into the messages of one digest."""

from __future__ import annotations

from collections.abc import Sequence

from .settings import Settings


def build_digest(items: Sequence[str], settings: Settings) -> list[str]:
    """Split items into messages of at most ``batch_size`` lines each.

    A ``batch_size`` of 0 puts every item in one message. Each message starts
    with the subject prefix and a count, then one item per line.
    """
    items = [item.strip() for item in items if item.strip()]
    if not items:
        return []
    size = settings.batch_size if settings.batch_size > 0 else len(items)
    chunks = [items[start : start + size] for start in range(0, len(items), size)]
    messages = []
    for number, chunk in enumerate(chunks, start=1):
        header = f"{len(chunk)} update{'s' if len(chunk) != 1 else ''}"
        if len(chunks) > 1:
            header += f" ({number}/{len(chunks)})"
        if settings.subject_prefix:
            header = f"{settings.subject_prefix} {header}"
        messages.append("\n".join([header, *(f"- {item}" for item in chunk)]))
    return messages


def delivery_attempts(settings: Settings) -> int:
    """How many times a message is tried before giving up."""
    return 1 + max(settings.retries, 0)
