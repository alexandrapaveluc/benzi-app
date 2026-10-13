import time
from threading import Lock
from typing import Any, Hashable


class TTLCache:
    """Pastreaza valori in memorie pentru un numar de secunde."""

    def __init__(self, ttl_seconds: int, max_items: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items: dict[Hashable, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: Hashable) -> Any | None:
        with self._lock:
            item = self._items.get(key)

            if item is None:
                return None

            expires_at, value = item

            if time.monotonic() >= expires_at:
                del self._items[key]
                return None

            return value

    def set(self, key: Hashable, value: Any) -> None:
        if self.ttl_seconds <= 0:
            return

        with self._lock:
            if len(self._items) >= self.max_items:
                self._remove_expired()

            if len(self._items) >= self.max_items:
                oldest_key = min(self._items, key=lambda k: self._items[k][0])
                del self._items[oldest_key]

            self._items[key] = (time.monotonic() + self.ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def _remove_expired(self) -> None:
        now = time.monotonic()
        expired = [key for key, (expires_at, _) in self._items.items() if now >= expires_at]

        for key in expired:
            del self._items[key]
