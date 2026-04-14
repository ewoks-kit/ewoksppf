import itertools
import time

import pytest
from ewokscore.task import Task
from ewoksutils.import_utils import qualname

from ..bindings import execute_graph


class Required(Task, input_names=["compute_time"], output_names=["required"]):
    def run(self):
        time.sleep(self.inputs.compute_time)
        self.outputs.required = True


class Optional(Task, input_names=["compute_time"], output_names=["optional"]):
    def run(self):
        time.sleep(self.inputs.compute_time)
        self.outputs.optional = True


class Gather(
    Task,
    input_names=["required1", "required2"],
    optional_input_names=["optional1", "optional2", "retained1", "retained2"],
    output_names=["cached"],
):
    def run(self):
        cached = self.get_input_values()
        print(f"\nDecider executed with inputs: {cached}")
        self.outputs.cached = cached


def workflow():
    nodes = [
        {
            "id": "required1",
            "task_type": "class",
            "task_identifier": qualname(Required),
        },
        {
            "id": "required2",
            "task_type": "class",
            "task_identifier": qualname(Required),
        },
        {
            "id": "optional1",
            "task_type": "class",
            "task_identifier": qualname(Optional),
        },
        {
            "id": "optional2",
            "task_type": "class",
            "task_identifier": qualname(Optional),
        },
        {
            "id": "retained1",
            "task_type": "class",
            "task_identifier": qualname(Optional),
        },
        {
            "id": "retained2",
            "task_type": "class",
            "task_identifier": qualname(Optional),
        },
        {
            "id": "gather",
            "task_type": "class",
            "task_identifier": qualname(Gather),
        },
    ]
    links = [
        {
            "source": "required1",
            "target": "gather",
            "data_mapping": [
                {"source_output": "required", "target_input": "required1"}
            ],
        },
        {
            "source": "required2",
            "target": "gather",
            "data_mapping": [
                {"source_output": "required", "target_input": "required2"}
            ],
        },
        {
            "source": "optional1",
            "target": "gather",
            "required": False,
            "cache_if_optional": True,
            "data_mapping": [
                {"source_output": "optional", "target_input": "optional1"}
            ],
        },
        {
            "source": "optional2",
            "target": "gather",
            "required": False,
            "cache_if_optional": True,
            "data_mapping": [
                {"source_output": "optional", "target_input": "optional2"}
            ],
        },
        {
            "source": "retained1",
            "target": "gather",
            "required": False,
            "cache_if_optional": False,
            "data_mapping": [
                {"source_output": "optional", "target_input": "retained1"}
            ],
        },
        {
            "source": "retained2",
            "target": "gather",
            "required": False,
            "cache_if_optional": False,
            "data_mapping": [
                {"source_output": "optional", "target_input": "retained2"}
            ],
        },
    ]
    return {"graph": {"id": "workflow"}, "nodes": nodes, "links": links}


def get_inputs(required, optional, retained):
    return [
        {"id": "required1", "name": "compute_time", "value": required},
        {"id": "required2", "name": "compute_time", "value": required},
        {"id": "optional1", "name": "compute_time", "value": optional},
        {"id": "optional2", "name": "compute_time", "value": optional},
        {"id": "retained1", "name": "compute_time", "value": retained},
        {"id": "retained2", "name": "compute_time", "value": retained},
    ]


_ORDER = list(itertools.permutations(["required", "optional", "retained"]))


@pytest.mark.parametrize("order", _ORDER, ids=["-".join(keys) for keys in _ORDER])
def test_ppf_workflow25(ppf_log_config, order):
    """Test input caching for different types of links executed in different orders."""
    compute_times = [0, 0.5, 1]
    inputs = get_inputs(**dict(zip(order, compute_times)))

    result = execute_graph(workflow(), pool_type="thread", inputs=inputs)
    cached = set(result["cached"])
    cached1 = {"required1", "required2", "optional1", "optional2", "retained1"}
    cached2 = {"required1", "required2", "optional1", "optional2", "retained2"}
    assert cached == cached1 or cached == cached2, cached
