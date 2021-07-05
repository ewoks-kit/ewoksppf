import logging
from ewokscore.hashing import UniversalHash
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
    presistent = bool(varinfo.get("root_uri", None))
    if presistent:
        inputs = {name: UniversalHash(uhash) for name, uhash in inputs.items()}
    task = instantiate_task(info["node_attrs"], varinfo=varinfo, inputs=inputs)

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
    if presistent:
        return task.output_uhashes
    else:
        return task.output_values
