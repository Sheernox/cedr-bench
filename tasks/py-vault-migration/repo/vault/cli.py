"""Offline vault administration."""
from __future__ import annotations
import argparse
from pathlib import Path
from .store import Store
from .importer import import_document
from .export import export
from .search import search
from .model import Vault
from recordkit.jsonio import read
from recordkit.audit import append

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--import-file", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--query", default="")
    parser.add_argument("--include-archived", action="store_true")
    parser.add_argument("--format", default="table", choices=("table", "json", "csv", "markdown"))
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args(argv)
    try:
        store = Store(args.path)
        vault = store.load() if args.path.exists() else Vault()
        if args.import_file:
            vault = import_document(vault, read(args.import_file), args.overwrite)
            store.save(vault)
            if args.audit:
                append(args.audit, "import", {"notes": len(vault.notes)})
        view = Vault(search(vault, args.query, args.include_archived), vault.extra)
        print(export(view, args.format), end="")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"vault: {exc}\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
