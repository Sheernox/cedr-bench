"""Command line entry point: read items from stdin, post or print the digest."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence

from .digest import build_digest, delivery_attempts
from .settings import load_settings
from .sources import ConfigError, from_args


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        settings = load_settings(argv)
    except ConfigError as exc:
        print(f"notify: {exc}", file=sys.stderr)
        return 2

    if from_args(argv).get("show_settings"):
        print(json.dumps(settings.as_dict(), sort_keys=True))
        return 0

    messages = build_digest(sys.stdin.read().splitlines(), settings)
    for message in messages:
        if settings.dry_run:
            print(message)
            print()
        else:
            _send(settings.channel, message, delivery_attempts(settings), settings.timeout)
    if not settings.quiet:
        print(f"notify: {len(messages)} message(s) for {settings.channel}", file=sys.stderr)
    return 0


def _send(channel: str, message: str, attempts: int, timeout: float) -> None:
    # Delivery is out of scope for this repository; the hosted service plugs in here.
    raise NotImplementedError(f"no transport configured for {channel}")


if __name__ == "__main__":
    sys.exit(main())
