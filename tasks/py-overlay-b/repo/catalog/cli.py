"""Offline import tool; preview has the same wire contract as import."""
from __future__ import annotations
import argparse
from pathlib import Path
from .storage import load, save
from .transport import read_page
from .preview import preview
from .export import export
from recordkit.audit import append

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--format", choices=("json", "csv", "table"), default="table")
    parser.add_argument("--query", default="")
    parser.add_argument("--audit", type=Path)
    parser.add_argument("pages", nargs="*", type=Path)
    args = parser.parse_args(argv)
    try:
        catalog = load(args.index)
        if args.preview:
            entries = preview(catalog.snapshot(), (read_page(path) for path in args.pages))
        else:
            for path in args.pages:
                catalog.ingest(read_page(path))
            if args.pages:
                save(args.index, catalog)
            entries = catalog.visible()
            if args.audit and args.pages:
                append(args.audit, "import", {"pages": len(args.pages), "visible": len(entries)})
        print(export(entries, args.format, args.query), end="")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"catalog: {exc}\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
