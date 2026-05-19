from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    """Return current UTC time for timezone-naive database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
