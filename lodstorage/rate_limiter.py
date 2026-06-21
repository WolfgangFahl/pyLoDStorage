"""
Created on 2024-08-24

@author: wf
"""

from functools import wraps

from ratelimit import limits, sleep_and_retry


class RateLimiter:
    """
    Wrap the @limits decorator in a new decorator
    """

    def __init__(self, calls_per_minute: int = None):
        if calls_per_minute is None:
            calls_per_minute = 60 * 1000 * 1000  # use an irrationally high value
        self.calls_per_minute = calls_per_minute

    def rate_limited(self, f: callable):
        # build the throttled decorator once so its call-budget state persists
        # across invocations (otherwise the budget resets on every call)
        throttle = sleep_and_retry(limits(calls=self.calls_per_minute, period=60)(f))

        @wraps(f)
        def wrapper(*args, **kwargs):
            return throttle(*args, **kwargs)

        return wrapper
