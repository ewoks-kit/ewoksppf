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
    profile_directory = info["profile_directory"]
    if args:
        kwargs.update(enumerate(args))

    task = instantiate_task(
        info["node_id"],
        info["node_attrs"],
        inputs=kwargs,
        varinfo=varinfo,
        execinfo=execinfo,
        profile_directory=profile_directory,
    )

    task.execute()

    return task.get_output_transfer_data()
