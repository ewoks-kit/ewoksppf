def run(value=None, limit=10, **kwargs):

    if value is None:
        raise RuntimeError("Missing argument 'value'!")
    if limit is None:
        raise RuntimeError("Missing argument 'limit'!")
    doContinue = "true"
    if value >= limit:
        doContinue = "false"
    return {"doContinue": doContinue}
