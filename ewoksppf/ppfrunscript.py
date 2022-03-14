from ewokscore.inittask import instantiate_task


INFOKEY = "_noinput"


def run(**inputs):
    """Main of actor execution.

    :param **kw: output hashes from previous tasks
    :returns dict: output hashes
    """
    info = inputs.pop(INFOKEY)
    varinfo = info["varinfo"]
    execinfo = info["execinfo"]

    task = instantiate_task(
        info["node_id"],
        info["node_attrs"],
        inputs=inputs,
        varinfo=varinfo,
        execinfo=execinfo,
    )

    task.execute()

    return task.output_transfer_data
