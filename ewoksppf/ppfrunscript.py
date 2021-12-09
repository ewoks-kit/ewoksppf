from ewokscore.inittask import instantiate_task


INFOKEY = "_noinput"


def run(**inputs):
    """Main of actor execution.

    :param **kw: output hashes from previous tasks
    :returns dict: output hashes
    """
    info = inputs.pop(INFOKEY)
    varinfo = info["varinfo"]

    task = instantiate_task(
        info["node_attrs"],
        varinfo=varinfo,
        inputs=inputs,
        node_id=info["node_id"],
    )

    task.execute()

    return task.output_transfer_data
