from ewokscore.inittask import instantiate_task


INFOKEY = "_noinput"


def run(*args, **kwargs):
    """Main of actor execution.

    :param **kw: output hashes from previous tasks
    :returns dict: output hashes
    """
    info = kwargs.pop(INFOKEY)
    varinfo = info["varinfo"]
    execinfo = info["execinfo"]
    if args:
        kwargs.update(enumerate(args))

    task = instantiate_task(
        info["node_id"],
        info["node_attrs"],
        inputs=kwargs,
        varinfo=varinfo,
        execinfo=execinfo,
    )

    task.execute()

    return task.output_transfer_data
