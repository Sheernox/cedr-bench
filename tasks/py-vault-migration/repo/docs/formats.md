# Vault file compatibility

Load accepts every shipped format, preserves order and identities, and is
read-only. Saving always emits version 4 atomically. JSON export uses that same
encoder; import accepts the same formats as load. Unknown future versions are
errors, never guessed to be the newest schema. Public Note, Vault, Store,
load/save, decode/encode and import_document signatures remain stable.

Version 0 is a bare list: title, text, optional pinned. IDs are legacy-1,
legacy-2, etc. A version 1 object contains notes with id, title, text, tags,
pinned and optional created (an offset-qualified ISO timestamp).
Version 3 replaced text/tags with body/labels and added per-note and envelope
extra dictionaries for extensions. The fixture directory also preserves samples
from historical writers that were never exported by the main application.

Version 4 adds archived (default false) to version 3. Missing pinned defaults
to false. created can be null or an offset-qualified ISO-8601 timestamp.
Empty body, title and label strings, duplicate labels and label order are
meaningful. Do not normalize these values during migration. No existing record
may acquire a different id or change pinned state just because it was saved.

Unknown JSON fields are extension data, not discardable noise. Historical
readers move unknown envelope/record fields into the corresponding extra dict.
Structural fields are not extension data. Explicit extra entries take precedence over same-named unknown fields. Current files also
retain unknown fields by moving them into extra on the next save.

Reject malformed records (wrong types, duplicate identities, invalid timestamps,
invalid dictionary indexes) with FormatError, including on save, before
replacing a file. Booleans are not integers. Saving must not borrow or mutate
caller-owned values. Failed update calls must leave the existing file intact.
Only title, body, labels, pinned and archived are editable via Store.update.
