from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generic, Iterable, Optional, TypeVar


T = TypeVar("T")


@dataclass
class Registry(Generic[T]):
    _items: Dict[str, T]

    def __init__(self):
        self._items = {}

    def register(self, key: str, item: T) -> None:
        if key in self._items:
            raise KeyError(f"Duplicate registry key: {key}")
        self._items[key] = item

    def get(self, key: str) -> T:
        try:
            return self._items[key]
        except KeyError as e:
            raise KeyError(f"Registry key not found: {key}") from e

    def maybe_get(self, key: str) -> Optional[T]:
        return self._items.get(key)

    def keys(self) -> Iterable[str]:
        return self._items.keys()

