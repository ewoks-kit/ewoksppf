import logging
from ewokscore.inittask import instantiate_task


INFOKEY = "_noinput"


logger = logging.getLogger(__name__)


def run(**inputs):
    """Main of actor execution.

    :param **kw: output hashes from previous tasks
    :returns dict: output hashes
    """
    info = inputs.pop(INFOKEY)
    log = info.get("enable_logging")
    varinfo = info["varinfo"]

    try:
        task = instantiate_task(
            info["node_attrs"],
            varinfo=varinfo,
            inputs=inputs,
            node_name=info["node_name"],
        )
    except Exception as e:
        if log:
            logger.error(
                "\nINSTANTIATE {}\n ATTRIBUTES: {}\n ERROR: {}".format(
                    info["node_name"],
                    info["node_attrs"],
                    e,
                ),
            )
        raise

    try:
        task.execute()
    except Exception as e:
        if log:
            logger.error(
                "\nEXECUTE {} {}\n INPUTS: {}\n ERROR: {}".format(
                    info["node_name"],
                    repr(task),
                    task.input_values,
                    e,
                ),
            )
        raise

    if log:
        logger.info(
            "\nEXECUTE {} {}\n INPUTS: {}\n OUTPUTS: {}".format(
                info["node_name"],
                repr(task),
                task.input_values,
                task.output_values,
            ),
        )

    return task.output_transfer_data
