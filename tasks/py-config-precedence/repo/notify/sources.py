"""Readers for each place a setting can come from.

Each reader returns a dict of field name to value for the fields that source
mentions. Fields a source does not mention are absent or None; the merge in
``settings.py`` decides what wins.
"""

from __future__ import annotations

import argparse
import tomllib
from collections.abc import Mapping, Sequence

from .defaults import FIELD_TYPES, env_name


class ConfigError(ValueError):
    """A setting could not be read. The message says where it came from."""


def from_args(argv: Sequence[str]) -> dict[str, object]:
    parser = argparse.ArgumentParser(prog="notify", add_help=True)
    parser.add_argument("--config", default=None, help="path to a TOML config file")
    parser.add_argument("--channel", default=None)
    parser.add_argument("--batch-size", dest="batch_size", type=int, default=None)
    parser.add_argument("--retries", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--quiet", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--dry-run", dest="dry_run", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--subject-prefix", dest="subject_prefix", default=None)
    parser.add_argument("--show-settings", dest="show_settings", action="store_true")
    return vars(parser.parse_args(list(argv)))


def from_env(environ: Mapping[str, str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for field, kind in FIELD_TYPES.items():
        name = env_name(field)
        raw = environ.get(name)
        if raw is None:
            continue
        try:
            values[field] = kind(raw)
        except ValueError as exc:
            raise ConfigError(f"{name}: cannot read {raw!r} as {kind.__name__}") from exc
    return values


def from_file(path: str) -> dict[str, object]:
    try:
        with open(path, "rb") as handle:
            document = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"{path}: no such config file") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}") from exc

    table = document.get("notify", {})
    if not isinstance(table, dict):
        raise ConfigError(f"{path}: [notify] must be a table")
    values: dict[str, object] = {}
    for key, value in table.items():
        if key not in FIELD_TYPES:
            raise ConfigError(f"{path}: unknown setting {key!r}")
        values[key] = _check_type(path, key, value)
    return values


def _check_type(path: str, key: str, value: object) -> object:
    kind = FIELD_TYPES[key]
    if kind is float and isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    if kind is int and isinstance(value, bool):
        raise ConfigError(f"{path}: {key} must be an integer")
    if not isinstance(value, kind):
        raise ConfigError(f"{path}: {key} must be {kind.__name__}")
    return value
