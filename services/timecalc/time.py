from time import time


def has_passed_24_hours(timestamp: int | None) -> bool:
    if timestamp is None:
        return False

    now = int(time())
    return now - timestamp >= 24 * 60 * 60