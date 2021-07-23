def run_incrementation(a=None, b=None, c=None, d=None, increment_value=None, **kwargs):

    if a is None:
        raise RuntimeError("Missing argument 'a'!")
    if b is None:
        raise RuntimeError("Missing argument 'b'!")
    if c is None:
        raise RuntimeError("Missing argument 'c'!")
    if d is None:
        raise RuntimeError("Missing argument 'd'!")
    if increment_value is None:
        raise RuntimeError("Missing argument 'increment_value'!")
    return {
        "a": a + increment_value,
        "b": increment_value,
        "c": c,
        "d": d,
    }


def no_processing(a=None, b=None, c=None, d=None, increment_value=None, **kwargs):
    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "increment_value": increment_value,
    }


def move_d_to_a(a=None, b=None, c=None, d=None, **kwargs):
    if a is None:
        raise RuntimeError("Missing argument 'a'!")
    if b is None:
        raise RuntimeError("Missing argument 'b'!")
    if c is None:
        raise RuntimeError("Missing argument 'c'!")
    if d is None:
        raise RuntimeError("Missing argument 'd'!")

    return {
        "a": d,
        "b": b,
        "c": c,
        "d": d,
    }
