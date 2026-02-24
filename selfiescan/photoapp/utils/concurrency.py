from django.core.cache import cache

MAX_CONCURRENT_FACE_SEARCH = 10
CACHE_KEY = "face_search_inflight"
TTL = 60  # safety net (seconds)

def try_acquire_slot():
    print("try acquiring slot")
    """
    Try to acquire a concurrency slot.
    Returns True if allowed, False if limit exceeded.
    """
    current = cache.get(CACHE_KEY)

    if current is None:
        cache.set(CACHE_KEY, 1, timeout=TTL)
        return True

    if current >= MAX_CONCURRENT_FACE_SEARCH:
        return False

    cache.incr(CACHE_KEY)
    return True


def release_slot():
    """
    Release a previously acquired slot.
    """
    try:
        cache.decr(CACHE_KEY)
    except Exception:
        pass

