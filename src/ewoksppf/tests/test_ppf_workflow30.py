import threading

import pytest
from ewokscore.task import Task
from ewoksutils.import_utils import qualname

from ewoksppf import execute_graph

_SAVED = list()
_LOCK = threading.Lock()


class ConfigTask(Task, output_names=["config"]):
    def run(self):
        self.outputs.config = {}


class LoopTask(
    Task,
    input_names=["i", "n"],
    optional_input_names=["config"],
    output_names=["i", "keep_looping"],
):
    def run(self):
        self.outputs.i = self.inputs.i + 1
        self.outputs.keep_looping = self.outputs.i < self.inputs.n


class SaveTask(Task, optional_input_names=["i", "config"], output_names=["result"]):
    def run(self):
        if self.missing_inputs.i:
            self.outputs.result = False
        else:
            with _LOCK:
                _SAVED.append(self.inputs.i)
            self.outputs.result = True


def workflow30(force_start_node: bool, n: int = 10):
    """Self-triggering "loop" node next to an independent "config" start node (issue #16).

    The "loop" node is started either by marking it explicitly as a start node
    or by adding a link from "config" to "loop".
    """
    loop_node = {
        "id": "loop",
        "task_type": "class",
        "task_identifier": qualname(LoopTask),
        "default_inputs": [{"name": "i", "value": 0}, {"name": "n", "value": n}],
    }
    if force_start_node:
        loop_node["force_start_node"] = True
    nodes = [
        {
            "id": "config",
            "task_type": "class",
            "task_identifier": qualname(ConfigTask),
        },
        loop_node,
        {
            "id": "save",
            "task_type": "class",
            "task_identifier": qualname(SaveTask),
        },
    ]
    links = [
        {
            "source": "loop",
            "target": "loop",
            "data_mapping": [{"source_output": "i", "target_input": "i"}],
            "conditions": [{"source_output": "keep_looping", "value": True}],
        },
        {
            "source": "loop",
            "target": "save",
            "data_mapping": [{"source_output": "i", "target_input": "i"}],
        },
        {
            "source": "config",
            "target": "save",
            "data_mapping": [{"source_output": "config", "target_input": "config"}],
        },
    ]
    if not force_start_node:
        links.append(
            {
                "source": "config",
                "target": "loop",
                "data_mapping": [{"source_output": "config", "target_input": "config"}],
            }
        )
    return {"graph": {"id": "workflow30"}, "nodes": nodes, "links": links}


@pytest.mark.parametrize("repeat", range(10))
@pytest.mark.parametrize("force_start_node", [False, True])
def test_workflow30(ppf_log_config, force_start_node, repeat):
    """Every iteration of the self-triggering "loop" node should be saved
    without "the pool is closed" errors (issue #16)."""
    _SAVED.clear()
    execute_graph(
        workflow30(force_start_node),
        pool_type="thread",
        scaling_workers=False,
    )
    assert sorted(_SAVED) == list(range(1, 11))
