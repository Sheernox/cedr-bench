# Pocket vault

An offline notes file suitable for scripts, exports and lightweight editors.
Run `python -m vault.cli FILE --format table` to list notes, or pass
`--import-file OTHER --overwrite` to merge one vault into another. JSON exports
are lossless interchange; Markdown and CSV are human-readable projections.

The storage contract is docs/formats.md; shipped formats live in fixtures/.
Run `python -m unittest discover -s tests` for local checks.
