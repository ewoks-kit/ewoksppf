import time
from . import SLEEP_TIME


def run(all_arguments=None):

    if all_arguments is None:
        raise RuntimeError("Missing argument 'all_arguments'!")
    time.sleep(SLEEP_TIME)
    all_arguments = dict(all_arguments)
    value = all_arguments["value"]
    value = value + 1
    all_arguments["value"] = value
    return {"all_arguments": all_arguments}
