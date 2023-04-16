import os
import time
from typing import Any

def parallel_sort(values, keys, reverse=False):
    s = sorted(enumerate(values), key=lambda k: keys[k], reverse=reverse)
    return [v for i, v in s]

def current_time_millis():
    return round(time.time() * 1000)

def dict_update(d1: dict, d2: dict, no_copy=False):
    if no_copy:
        d1.update(d2)
    else:
        d1 = d1.copy()
        d1.update(d2)
    return d1

class AutoPopulate:
    def __init__(self, **kwargs) -> None:
        for k, type_str in self.__annotations__.items():
            if k in kwargs:
                setattr(self, k, kwargs[k])
            else:
                setattr(self, k, None)
