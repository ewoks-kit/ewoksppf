"""Dranspose is a WFM used at MAX-IV: https://github.com/felix-engelmann/dranspose

It runs map-reduce style workflows. This script is an example of the Ewoks equivalent.
"""

import os
import time
import random

import numpy
from silx.io import h5py_utils

from ewoksppf import execute_graph
from ewokscore.task import Task


class GenerateData(
    Task,
    input_names=["nblocks", "block_size"],
    optional_input_names=["block_index"],
    output_names=["image_stack", "block_index", "finished"],
):

    def run(self):
        t0 = time.perf_counter()
        block_index = self.get_input_value("block_index", 0)
        block_size = self.inputs.block_size
        start_value = block_index * block_size
        values = numpy.arange(start_value, start_value + block_size, dtype=numpy.int32)
        image_stack = numpy.broadcast_to(
            values.reshape(block_size, 1, 1), (block_size, 4096, 4096)
        )
        self.outputs.image_stack = image_stack.copy()
        self.outputs.block_index = block_index + 1
        self.outputs.finished = self.outputs.block_index >= self.inputs.nblocks
        t1 = time.perf_counter()
        print(f"{block_size/(t1-t0)} images/sec")


class IntegrateData(
    Task,
    input_names=["image_stack", "block_index"],
    optional_input_names=["axis", "delay"],
    output_names=["pattern_stack", "block_index"],
):

    def run(self):
        image_axis = self.get_input_value("axis", 0)
        self.outputs.pattern_stack = self.inputs.image_stack.sum(axis=image_axis + 1)
        self.outputs.block_index = self.inputs.block_index

        delay = self.get_input_value("delay", 0)
        if delay:
            time.sleep(random.uniform(delay, delay * 1.5))
        else:
            time.sleep(random.uniform(0, 0.1))


class SaveData(
    Task,
    input_names=["data_stack", "block_index", "filename"],
    output_names=["hdf5_url"],
):

    def run(self):
        filename = os.path.abspath(self.inputs.filename)
        block_index = self.inputs.block_index
        data_stack = self.inputs.data_stack
        block_size = len(data_stack)

        start_index = (block_index - 1) * block_size
        stop_index = start_index + block_size

        with h5py_utils.open_item(filename, "/", mode="a") as f:
            ndim0_required = stop_index

            # Make sure dataset exists and is large enough
            if "data" in f:
                dset = f["data"]
                if len(dset) < ndim0_required:
                    dset.resize(ndim0_required, axis=0)
            else:
                data_shape = data_stack.shape[1:]
                dset = f.create_dataset(
                    "data",
                    shape=(ndim0_required, *data_shape),
                    maxshape=(None, *data_shape),
                    dtype=data_stack.dtype,
                )

            dset[start_index:stop_index, ...] = data_stack

        self.outputs.hdf5_url = (
            f"silx://{filename}?path=/data&slice={start_index},{stop_index}"
        )
        print(f"Saved {self.outputs.hdf5_url}")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("pypushflow").setLevel(logging.WARNING)

    nodes = [
        {
            "id": "generate",
            "task_type": "class",
            "task_identifier": "__main__.GenerateData",
        },
        {
            "id": "integrate",
            "task_type": "class",
            "task_identifier": "__main__.IntegrateData",
        },
        {
            "id": "save",
            "task_type": "class",
            "task_identifier": "__main__.SaveData",
        },
    ]
    links = [
        {
            "source": "generate",
            "target": "generate",
            "data_mapping": [
                {"source_output": "block_index", "target_input": "block_index"}
            ],
            "conditions": [{"source_output": "finished", "value": False}],
        },
        {
            "source": "generate",
            "target": "integrate",
            "data_mapping": [
                {"source_output": "image_stack", "target_input": "image_stack"},
                {"source_output": "block_index", "target_input": "block_index"},
            ],
        },
        {
            "source": "integrate",
            "target": "save",
            "data_mapping": [
                {"source_output": "pattern_stack", "target_input": "data_stack"},
                {"source_output": "block_index", "target_input": "block_index"},
            ],
        },
    ]
    workflow = {"graph": {"id": "test"}, "nodes": nodes, "links": links}
    inputs = [
        {"id": "generate", "name": "nblocks", "value": 10},
        {"id": "generate", "name": "block_size", "value": 3},
        {"id": "integrate", "name": "axis", "value": 1},
        {
            "id": "integrate",
            "name": "delay",
            "value": 0,
        },  # add fake time to integration
        {"id": "save", "name": "filename", "value": "result.h5"},
    ]

    if os.path.exists("result.h5"):
        os.unlink("result.h5")

    result = execute_graph(
        workflow,
        inputs=inputs,
        pool_type="process",  # thread, process, gevent
        scaling_workers=False,
        max_workers=16,
        raise_error=True,
    )
