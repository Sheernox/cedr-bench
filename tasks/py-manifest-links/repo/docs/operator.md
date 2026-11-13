# Packtree operator console

The operator console consumes a local JSON document. It makes no network
requests. Launch `python3 -m packtree.cli examples/session.json totals` from the
repository root. `report` prints the default view; `views` lists view settings.
`audit` prints successful operator receipts and `snapshot` prints a detached
session document. Diagnostics go to stderr with exit status 2.

## Views

A view stores a name, a JSON filter, a sort field, a sort direction and a page
size. Page sizes range from 1 to 1000. A view's page index is zero-based.
Filters support exact equality, inequality, text containment, list membership,
and inclusive integer ranges. `all`, `any` and `not` combine predicates.
Text containment ignores case; equality preserves type and spelling. Missing
fields are excluded from equality and range tests. An empty filter selects
all rows. Filter compilation checks every branch before scanning data.

## Reports

Text reports collapse whitespace in cells and truncate long cells with three
periods. HTML reports escape both headings and values. HTML includes a caption
and column-header scopes for assistive technology. CSV transport uses Unix
newlines and standard quoting. JSONL errors identify the line number without
including record contents.

## Audit

An audit export is a hash chain of timestamped actions. It detects accidental
edits or missing records, but it is not a signature. Timestamps need an ISO-8601
offset. Restoring an audit validates every digest and predecessor. Reports
return copies so editing a downloaded document cannot change an active session.

## Review

The diff report compares rows by identity and distinguishes a missing field
from a field containing null. Applying a diff requires an exact base value.
Reverse diffs can undo a review in memory. These reports do not provide domain
rollback; each service's own transaction contract defines when data is accepted.
