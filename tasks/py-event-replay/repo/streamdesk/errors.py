"""Stable exception classes for clients and transport adapters."""
class InvalidEvent(ValueError):
    """An event or account transition is invalid."""
class Conflict(ValueError):
    """An event identity was reused with different contents."""
class InvalidCheckpoint(ValueError):
    """A checkpoint is not a supported, consistent document."""
