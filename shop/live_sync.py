import time
import threading
from collections import deque

_lock = threading.Lock()
_store_version = time.time()
_recent_events = deque(maxlen=100)


def record_change(entity_type, entity_id, action="updated", details=None):
    """
    Record a modification in the store (e.g. from Django Admin)
    and increment the store revision timestamp.
    """
    global _store_version
    with _lock:
        _store_version = time.time()
        event = {
            "version": _store_version,
            "timestamp": _store_version,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "action": action,
            "details": details or {},
        }
        _recent_events.append(event)
        return event


def get_current_version():
    with _lock:
        return _store_version


def get_latest_event():
    with _lock:
        return _recent_events[-1] if _recent_events else None


def get_events_since(since_version):
    try:
        since_val = float(since_version)
    except (ValueError, TypeError):
        since_val = 0.0

    with _lock:
        return [e for e in _recent_events if e["timestamp"] > since_val]
