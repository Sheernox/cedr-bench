"""Release build, inventory and verification commands."""
from __future__ import annotations
import argparse
from pathlib import Path
from .rules import Policy
from .fast import inventory
from .build import build,dry_run
from .verify import verify,Required
from recordkit.jsonio import pretty

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("build","inventory","verify","plan"))
    parser.add_argument("root",type=Path)
    parser.add_argument("--policy",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--required",action="append",default=[])
    args=parser.parse_args(argv)
    try:
        lines=args.policy.read_text().splitlines() if args.policy else []
        if args.command=="inventory":
            print(pretty(inventory(args.root,Policy(lines))),end="")
        elif args.command=="plan":
            print(pretty(dry_run(args.root,lines)),end="")
        elif args.command=="verify":
            report=verify(args.root.read_bytes(),[Required(name) for name in args.required])
            print(report.json(),end="")
            return 0 if report.ok else 1
        else:
            if args.output is None:
                parser.error("build requires --output")
            print(pretty(build(args.root,lines,args.output)),end="")
    except (ValueError,OSError) as exc:
        parser.exit(2,f"release: {exc}\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
