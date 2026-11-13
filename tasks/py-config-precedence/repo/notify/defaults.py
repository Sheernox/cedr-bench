"""The settings notify knows about, their types and their defaults."""

from __future__ import annotations

FIELD_TYPES: dict[str, type] = {
    "channel": str,
    "batch_size": int,
    "retries": int,
    "timeout": float,
    "quiet": bool,
    "dry_run": bool,
    "subject_prefix": str,
}

DEFAULTS: dict[str, object] = {
    "channel": "#general",
    "batch_size": 50,
    "retries": 3,
    "timeout": 10.0,
    "quiet": False,
    "dry_run": False,
    "subject_prefix": "[digest]",
}

ENV_PREFIX = "NOTIFY_"


def env_name(field: str) -> str:
    return ENV_PREFIX + field.upper()
