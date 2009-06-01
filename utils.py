from google.appengine.api import memcache

import functools
import logging

def memoize(keyformat, time=60):
    """Decorator to memoize functions using memcache."""
    def decorator(fxn):
        def wrapper(*args, **kwargs):
            key = keyformat % args[0:keyformat.count('%')]
            data = memcache.get(key)
            if data is not None:
                return data
            data = fxn(*args, **kwargs)
            memcache.set(key, data, time)
            return data
        return wrapper
    return decorator
	
def selfmemoize(keyformat, time=60):
    """Decorator to memoize functions using memcache."""
    def decorator(fxn):
        def wrapper(self, *args, **kwargs):
            key = keyformat % args[0:keyformat.count('%')]
            data = memcache.get(key)
            if data is not None:
                return data
            data = fxn(self, *args, **kwargs)
            memcache.set(key, data, time)
            return data
        return wrapper
    return decorator
