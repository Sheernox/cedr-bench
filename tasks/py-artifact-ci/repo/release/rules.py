"""Parse ordered file-selection rules from a release policy."""
from __future__ import annotations
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from collections.abc import Iterable

@dataclass(frozen=True)
class Rule:
    pattern: str
    include: bool
    directory: bool
    anchored: bool

    def matches(self, path: str, is_dir: bool = False) -> bool:
        target = PurePosixPath(path).name
        if self.directory:
            return is_dir and fnmatchcase(target, self.pattern)
        return fnmatchcase(target, self.pattern)

class Policy:
    def __init__(self, lines: Iterable[str]) -> None:
        self.rules = parse(lines)

    def included(self, path: str, is_dir: bool = False) -> bool:
        for rule in self.rules:
            if rule.matches(path,is_dir):
                return rule.include
        return True

def parse(lines: Iterable[str]) -> tuple[Rule,...]:
    rules = []
    for line in lines:
        raw = line.rstrip("\r\n")
        if not raw or raw.startswith("#"):
            continue
        include = raw.startswith("!")
        if include:
            raw = raw[1:]
        elif raw.startswith("\\#") or raw.startswith("\\!"):
            raw = raw[1:]
        anchored = raw.startswith("/")
        directory = raw.endswith("/")
        pattern = raw.strip("/")
        if not pattern:
            raise ValueError("empty release pattern")
        rules.append(Rule(pattern,include,directory,anchored))
    return tuple(rules)
