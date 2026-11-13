# Offline order operations

The order session separates three concerns: an editable basket, accepted
historical receipts, and stock reservations. Merchandise pricing remains in
`docs/pricing.md`; parcel estimates are separate and never alter a Quote.
No module performs network requests or chooses an output directory.

## Baskets

The editor retains each entered line, including zero quantities and repeated
SKUs. Moving a line changes its display position. Removing a line returns a
copy so an operator can implement undo. Setting coupons retains typed spelling;
pricing decides normalization and validation. Saving a basket produces version
2 and leaves the editor live. Clearing resets both lines and coupons.

## History

Accepted receipts retain their numeric amounts independently of current catalog
prices. A historical receipt must add up before it enters history. History IDs
are unique; timestamps must have an ISO-8601 offset. Reports group by UTC date.
Order exports are detached copies, safe to edit outside the active session.

## Stock

Stock arrivals are whole nonnegative units. Reservations combine repeated SKUs
before checking availability. A failed reservation holds no stock. Releasing a
reservation frees availability; shipping reduces on-hand stock and removes the
reservation. Reservation IDs cannot be reused until the old hold is removed.

## Transport

JSONL imports report malformed line numbers without printing the record.
Bulk inspection retains per-order errors for review. Bulk upgrade returns no
result if any order fails. Unknown SKU and coupon validation happens during
pricing, so decoding an old product code is safe even after catalog changes.
CSV and HTML are report formats, not persistence formats.

## Shipping

Parcel capacity is measured in whole grams. A line can be divided among parcels
while preserving entered order. A single item above capacity rejects the plan.
Rate bands are ascending and inclusive at their upper boundary. A fragile
surcharge applies once per parcel. Empty plans cost zero. Profile values are
copied on insertion and lookup.

## Command adapter

Run `node src/cli.ts products-csv` for the catalog, or pass a JSON order file
to `quote`, `receipt`, `decode`, or `reprice`. A file of `-` reads stdin.
`--compact` controls JSON whitespace. The command writes no files implicitly.
