"""Streaming counters for verbose command summaries."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Iterable
import math

@dataclass
class Moments:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def add(self, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError("statistics require finite values")
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (value - self.mean)
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)

    @property
    def variance(self) -> float:
        return self.m2 / self.count if self.count else 0.0

    def document(self) -> dict[str, int | float | None]:
        return {"count": self.count, "mean": self.mean, "variance": self.variance,
                "min": self.minimum, "max": self.maximum}

@dataclass
class Counter:
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, key: str, amount: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + amount

    def merge(self, other: Counter) -> None:
        for key, value in other.counts.items():
            self.add(key, value)

    def top(self, limit: int = 10) -> list[tuple[str, int]]:
        if limit < 0:
            raise ValueError("limit must not be negative")
        return sorted(self.counts.items(), key=lambda item: (-item[1], item[0]))[:limit]

def sizes(values: Iterable[bytes]) -> Moments:
    result = Moments()
    for value in values:
        result.add(len(value))
    return result
