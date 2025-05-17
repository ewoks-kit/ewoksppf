def run(name, **kwargs):
    reply = None
    # This actor throws an exception
    raise RuntimeError("Intentional error in pythonErrorHandlerTest!")
    if name is not None:
        reply = "Hello " + name + "!"

    return {"reply": reply}
