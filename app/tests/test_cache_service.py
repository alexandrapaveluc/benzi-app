from app.services import cache_service
from app.services.cache_service import TTLCache


def test_returns_saved_value():
    cache = TTLCache(ttl_seconds=60)

    cache.set("cheie", 42)

    assert cache.get("cheie") == 42


def test_missing_key_returns_none():
    assert TTLCache(ttl_seconds=60).get("lipsa") is None


def test_value_expires(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(cache_service.time, "monotonic", lambda: now[0])

    cache = TTLCache(ttl_seconds=60)
    cache.set("cheie", 42)

    now[0] += 59
    assert cache.get("cheie") == 42

    now[0] += 2
    assert cache.get("cheie") is None


def test_zero_ttl_disables_cache():
    cache = TTLCache(ttl_seconds=0)

    cache.set("cheie", 42)

    assert cache.get("cheie") is None


def test_oldest_item_is_removed_when_full():
    cache = TTLCache(ttl_seconds=60, max_items=2)

    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3
