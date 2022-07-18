import time
from . import SLEEP_TIME


def run(c=None, **kwargs):

    time.sleep(SLEEP_TIME)
    if c is None:
        raise RuntimeError("Missing argument 'c'!")
    d = c + 1
    return {"d": d}
