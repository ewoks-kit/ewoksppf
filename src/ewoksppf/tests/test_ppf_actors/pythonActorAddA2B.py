import time
from . import SLEEP_TIME


def run(a=None, **kwargs):

    time.sleep(SLEEP_TIME)
    if a is None:
        raise RuntimeError("Missing argument 'value'!")
    b = a + 1
    return {"b": b}
