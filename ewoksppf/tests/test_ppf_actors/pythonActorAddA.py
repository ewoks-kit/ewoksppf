def run(a=None, **kwargs):
    if a is None:
        raise RuntimeError("Missing argument 'a'!")
    a += 1
    print(f"In AddA, a={a}")
    if a == 5:
        print(f"a reached {a}!")
        a_is_5 = True
    else:
        a_is_5 = False
    return {"a": a, "a_is_5": a_is_5}
