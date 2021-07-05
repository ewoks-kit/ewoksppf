import time
from . import SLEEP_TIME


def run(b=None, **kwargs):

    time.sleep(SLEEP_TIME)
    if b is None:
        raise RuntimeError("Missing argument 'value'!")
    c = b + 1
    return {"c": c}
