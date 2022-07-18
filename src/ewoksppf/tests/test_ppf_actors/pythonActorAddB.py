def run(b=None, **kwargs):
    if b is None:
        raise RuntimeError("Missing argument 'b'!")
    b += 1
    print(f"In AddB, b={b}")
    if b == 4:
        print(f"b reached {b}!")
        b_is_4 = True
    else:
        b_is_4 = False
    return {"b": b, "b_is_4": b_is_4}
