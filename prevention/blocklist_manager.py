# prevention/blocklist_manager.py

"""
In-memory blocklist manager for Phase 1 testing.

This module keeps blocked IPs in memory.
Entries automatically expire after BLOCKLIST_EXPIRY_MINUTES.
"""

from datetime import datetime, timedelta

from config import BLOCKLIST_EXPIRY_MINUTES


# IP address -> expiry datetime
_blocklist = {}


def is_blocked(source_ip: str) -> bool:
    """Check whether an IP is currently blocked."""

    expiry = _blocklist.get(source_ip)

    if expiry is None:
        return False

    # Remove expired entry
    if datetime.now() > expiry:
        del _blocklist[source_ip]
        return False

    return True


def add_to_blocklist(source_ip: str):
    """Add an IP to the blocklist with an expiry time."""

    _blocklist[source_ip] = (
        datetime.now()
        + timedelta(minutes=BLOCKLIST_EXPIRY_MINUTES)
    )


def get_blocklist() -> dict:
    """Return a copy of the current blocklist."""

    return dict(_blocklist)


def reset_blocklist():
    """Clear the blocklist. Useful for testing."""

    _blocklist.clear()