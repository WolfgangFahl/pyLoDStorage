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
        @wraps(f)
        def wrapper(*args, **kwargs):
            @sleep_and_retry
            @limits(calls=self.calls_per_minute, period=60)
            def rate_limited_function():
                return f(*args, **kwargs)

            return rate_limited_function()

        return wrapper
