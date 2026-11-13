"""Read-only load and atomic save, including the legacy read interface."""
from __future__ import annotations
from pathlib import Path
from .model import Vault
from .codec import decode, encode, FormatError
from recordkit.jsonio import read, atomic_write

class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> Vault:
        return decode(read(self.path))

    def save(self, vault: Vault) -> None:
        atomic_write(self.path, encode(vault))

    def update(self, identity: str, **fields: object) -> Vault:
        vault = self.load()
        note = vault.get(identity)
        for key, value in fields.items():
            if key not in {"title", "body", "labels", "pinned", "archived"}:
                raise ValueError(f"field is not editable: {key}")
            setattr(note, key, value)
        vault.replace(note)
        self.save(vault)
        return vault

def load(path: str | Path) -> Vault:
    return Store(path).load()

def save(path: str | Path, vault: Vault) -> None:
    Store(path).save(vault)
