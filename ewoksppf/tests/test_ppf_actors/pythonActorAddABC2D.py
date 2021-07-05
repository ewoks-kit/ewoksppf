import time
from . import SLEEP_TIME


def run(a=None, b=None, c=None, **kwargs):

    time.sleep(SLEEP_TIME)
    if a is None:
        raise RuntimeError("Missing argument 'a'!")
    if b is None:
        raise RuntimeError("Missing argument 'b'!")
    if c is None:
        raise RuntimeError("Missing argument 'c'!")
    d = a + b + c
    return {"d": d}
