"""Integer windows avoid wall-clock or timezone ambiguity."""
from .errors import InvalidWindow

def validate_window(start: int, end: int) -> None:
    if type(start) is not int or type(end) is not int or start > end:
        raise InvalidWindow("expected start <= end, integer ticks")

def clip(row: dict, start: int, end: int) -> dict | None:
    lo, hi = max(start, row["start"]), min(end, row["end"])
    if lo >= hi:
        return None
    return {**row, "start": lo, "end": hi}
