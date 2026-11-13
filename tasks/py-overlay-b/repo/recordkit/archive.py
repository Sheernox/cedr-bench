"""Deterministic ZIP interchange with path and integrity validation."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable
from io import BytesIO
import hashlib
import zipfile
from .paths import relative_name, beneath
from .jsonio import canonical, decode

@dataclass(frozen=True)
class Member:
    name: str
    data: bytes
    executable: bool = False

    def descriptor(self) -> dict[str, object]:
        return {"name": self.name, "size": len(self.data),
                "sha256": hashlib.sha256(self.data).hexdigest(),
                "executable": self.executable}

def pack(members: Iterable[Member]) -> bytes:
    rows = sorted(members, key=lambda member: member.name)
    seen: set[str] = set()
    for member in rows:
        name = relative_name(member.name)
        if name != member.name or name in seen or name == "MANIFEST.json":
            raise ValueError("duplicate, reserved or noncanonical archive name")
        seen.add(name)
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for member in rows:
            info = zipfile.ZipInfo(member.name, (2000,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if member.executable else 0o100644) << 16
            archive.writestr(info, member.data)
        info = zipfile.ZipInfo("MANIFEST.json", (2000,1,1,0,0,0))
        info.external_attr = 0o100644 << 16
        archive.writestr(info, canonical([row.descriptor() for row in rows]))
    return buffer.getvalue()

def unpack(raw: bytes, max_bytes: int = 64*1024*1024) -> list[Member]:
    result: list[Member] = []
    seen: set[str] = set()
    total = 0
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        manifest = decode(archive.read("MANIFEST.json").decode("utf-8"))
        for info in archive.infolist():
            if info.filename == "MANIFEST.json":
                continue
            name = relative_name(info.filename)
            if name != info.filename or name in seen or info.is_dir():
                raise ValueError("duplicate or noncanonical archive member")
            seen.add(name)
            total += info.file_size
            if total > max_bytes:
                raise ValueError("archive exceeds uncompressed size limit")
            mode = info.external_attr >> 16
            if mode & 0o170000 not in (0,0o100000):
                raise ValueError("archive member is not a regular file")
            result.append(Member(name,archive.read(info),bool(mode & 0o111)))
    result.sort(key=lambda member: member.name)
    if [row.descriptor() for row in result] != manifest:
        raise ValueError("archive manifest does not match contents")
    return result

def extract(raw: bytes, root: Path) -> int:
    members = unpack(raw)
    destinations = [(beneath(root,member.name),member) for member in members]
    for path, member in destinations:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(member.data)
        path.chmod(0o755 if member.executable else 0o644)
    return len(members)

def from_directory(root: Path) -> list[Member]:
    result: list[Member] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            result.append(Member(path.relative_to(root).as_posix(),path.read_bytes(),
                                 bool(path.stat().st_mode & 0o111)))
    return result
