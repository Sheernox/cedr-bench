"""Compatibility path helpers. These operate on names, not manifests or links."""
from .errors import PathError

def normalize(path: str) -> str:
    """Collapse lexical dot segments in a relative POSIX path."""
    if not isinstance(path, str) or path.startswith("/") or "\0" in path:
        raise PathError("expected a relative package path")
    stack = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not stack:
                raise PathError("path escapes package root")
            stack.pop()
        else:
            stack.append(part)
    return "/".join(stack)

def canonical(path: str) -> bool:
    try:
        return bool(path) and normalize(path) == path and not path.endswith("/")
    except PathError:
        return False
