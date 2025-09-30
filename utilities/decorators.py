from functools import lru_cache
import time


def ttl_cache(ttl_seconds):
    def decorator(func):
        # Create a separate cache for storing timestamps
        cache_timestamps = {}

        @lru_cache(maxsize=32)
        def cached_with_timestamp(*args):
            result = func(*args)
            return result

        def wrapper(*args):
            # Check if the cache for this function call has expired
            if args in cache_timestamps:
                if time.time() - cache_timestamps[args] > ttl_seconds:
                    cached_with_timestamp.cache_clear()
                    cache_timestamps.pop(args, None)  # Remove expired entry from timestamp cache

            # Call the cached function and store the current time as the timestamp
            result = cached_with_timestamp(*args)
            cache_timestamps[args] = time.time()  # Update the timestamp for the cache
            return result

        return wrapper
    return decorator
