class InvalidRow(ValueError):
    """The input row violates the wire format."""
class InvalidWindow(ValueError):
    """Window boundaries must be integer ticks in ascending order."""
class RevisionConflict(ValueError):
    """An ID and revision identify two different rows."""
