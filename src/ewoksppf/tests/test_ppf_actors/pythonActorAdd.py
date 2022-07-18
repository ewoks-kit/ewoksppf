import time
from . import SLEEP_TIME


def run(value=None, **kwargs):

    time.sleep(SLEEP_TIME)
    if value is None:
        raise RuntimeError("Missing argument 'value'!")
    value = value + 1
    return {"value": value}
