from datetime import timedelta
from time import time

def get_interval_now(timestamp) -> str:
    now = int(time() )

    timestamp_diff = now - timestamp

    timedelta_diff = str( timedelta(seconds=timestamp_diff) )

    return timedelta_diff

def has_passed_24_hours(timestamp: int) -> bool:
    now = int(time())
    return now - timestamp >= 24 * 60 * 60