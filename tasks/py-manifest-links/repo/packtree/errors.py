"""Public boundary errors."""
class ManifestError(ValueError):
    """The manifest structure is invalid."""
class PathError(ValueError):
    """A selection cannot be resolved inside the package."""
class ExportConflict(ValueError):
    """Different files map to the same output name."""
