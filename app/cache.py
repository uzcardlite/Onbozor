import time
import logging

logger = logging.getLogger(__name__)

_store: dict[str, tuple[float, any]] = {}


def get(key: str):
    if key not in _store:
        return None
    expires, value = _store[key]
    if time.time() > expires:
        del _store[key]
        return None
    return value


def set(key: str, value, ttl: int = 300):
    _store[key] = (time.time() + ttl, value)


def delete(key: str):
    _store.pop(key, None)


def invalidate_prefix(prefix: str):
    keys = [k for k in _store if k.startswith(prefix)]
    for k in keys:
        del _store[k]
