"""Resolve the effective settings from flags, environment, file and defaults."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .defaults import DEFAULTS, env_name
from .sources import from_args, from_env, from_file


@dataclass(frozen=True)
class Settings:
    channel: str
    batch_size: int
    retries: int
    timeout: float
    quiet: bool
    dry_run: bool
    subject_prefix: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def load_settings(
    argv: Sequence[str],
    environ: Mapping[str, str] | None = None,
    config_path: str | None = None,
) -> Settings:
    """Return the settings for one run.

    ``environ`` is the environment to read; leave it out to use the process
    environment. ``config_path`` is the file to read when neither ``--config``
    nor ``NOTIFY_CONFIG`` names one.
    """
    environ = environ or os.environ
    args = from_args(argv)
    env = from_env(environ)
    path = args.get("config") or environ.get(env_name("config")) or config_path
    file_values = from_file(path) if path else {}

    resolved = {
        field: _pick(args.get(field), env.get(field), file_values.get(field), default)
        for field, default in DEFAULTS.items()
    }
    return Settings(**resolved)


def _pick(*candidates: object) -> object:
    # Unset values arrive as None or empty, so the first real value wins.
    for value in candidates:
        if value:
            return value
    return candidates[-1]
