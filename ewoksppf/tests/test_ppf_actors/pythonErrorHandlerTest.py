def run(name, **kwargs):

    reply = None
    # This actor throws an exception
    raise RuntimeError("Runtime error in pythonErrorHandlerTest.py!")
    if name is not None:
        reply = "Hello " + name + "!"

    return {"reply": reply}
