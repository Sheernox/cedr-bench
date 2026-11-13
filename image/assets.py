"""Fetch immutable, checksum-verified public font and browser archives at build time."""
from __future__ import annotations

import hashlib
import io
import shutil
import urllib.request
from pathlib import Path
from zipfile import ZipFile

ASSETS = [
    ("https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip",
     "9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e", "inter"),
    ("https://github.com/adobe-fonts/source-serif/releases/download/4.005R/source-serif-4.005_Desktop.zip",
     "549fdb8f9a682bd06944298621404969f6de77c2e422ff3b8244a1dcd6a0c425", "serif"),
    ("https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
     "6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf", "mono"),
    ("https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/1194/chromium-linux.zip",
     "5ad70cf662e7090354edbe84e1a01ac531fd217f37f5001f0d2efbe0d152b396", "browser"),
]


def main() -> None:
    fonts = Path("/usr/local/share/fonts/bench")
    fonts.mkdir(parents=True, exist_ok=True)
    for url, checksum, kind in ASSETS:
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != checksum:
            raise ValueError(f"Checksum mismatch for {kind}")
        with ZipFile(io.BytesIO(data)) as archive:
            for item in archive.infolist():
                name = item.filename
                if kind == "browser":
                    if item.is_dir():
                        continue
                    if Path(name).is_absolute() or ".." in Path(name).parts:
                        raise ValueError("Unsafe archive path")
                    target = Path("/opt/chromium") / name
                elif ((kind == "inter" and name.startswith("extras/ttf/Inter-")) or
                      (kind == "serif" and "/TTF/SourceSerif4-" in name) or
                      (kind == "mono" and name.startswith("fonts/ttf/JetBrainsMono-"))) and name.endswith(".ttf"):
                    target = fonts / Path(name).name
                else:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, target.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
                mode = item.external_attr >> 16
                target.chmod(0o755 if mode & 0o111 else 0o644)


if __name__ == "__main__":
    main()
