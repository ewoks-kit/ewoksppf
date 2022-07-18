import time
from . import SLEEP_TIME


def run(name, **kwargs):

    time.sleep(SLEEP_TIME)
    reply = None
    if name is not None:
        reply = "Hello " + name + "!"
    return {"reply": reply}
