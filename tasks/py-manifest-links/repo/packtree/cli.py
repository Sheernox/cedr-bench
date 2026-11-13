"""Read a session document and run one offline operator command.

No state is saved implicitly. A caller may redirect snapshot output to a new
file after reviewing it; failures go to stderr and return an exit status.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .commands import Commands, CommandError
from .session import Session
from .wire import WireError, read_document


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Offline session reports")
    result.add_argument("document", type=Path)
    result.add_argument("command", choices=["totals", "views", "report", "audit", "snapshot"])
    result.add_argument("--view")
    result.add_argument("--page", type=int)
    result.add_argument("--action")
    result.add_argument("--compact", action="store_true")
    return result


def open_session(document: dict) -> Session:
    return Session(document)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        with args.document.open(encoding="utf-8") as stream:
            session = open_session(read_document(stream))
        arguments = {key: value for key, value in {"view": args.view, "page": args.page, "action": args.action}.items() if value is not None}
        result = Commands(session).execute(args.command, arguments)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=None if args.compact else 2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"cannot run {args.command}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
