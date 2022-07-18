def run(value=None, **kwargs):

    if value is None:
        raise RuntimeError("Missing argument 'value'!")
    value += 1
    return {
        "value": value,
    }
