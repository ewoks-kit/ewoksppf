import threading

import pytest
from ewokscore.graph import analysis
from ewokscore.graph import load_graph
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
    output_names=["i", "keep_looping"],
):
    def run(self):
        self.outputs.i = self.inputs.i + 1
        self.outputs.keep_looping = self.outputs.i < self.inputs.n


class SaveTask(Task, input_names=["i", "config"], output_names=["result"]):
    def run(self):
        with _LOCK:
            _SAVED.append(self.inputs.i)
        self.outputs.result = True


def workflow31(required_loop_link: bool, n: int = 10):
    """Self-triggering "loop" node and an independent "config" node which
    both provide required inputs to "save" (issue #16)."""
    loop_to_save = {
        "source": "loop",
        "target": "save",
        "data_mapping": [{"source_output": "i", "target_input": "i"}],
    }
    if required_loop_link:
        loop_to_save["required"] = True
    nodes = [
        {
            "id": "config",
            "task_type": "class",
            "task_identifier": qualname(ConfigTask),
        },
        {
            "id": "loop",
            "force_start_node": True,
            "task_type": "class",
            "task_identifier": qualname(LoopTask),
            "default_inputs": [{"name": "i", "value": 0}, {"name": "n", "value": n}],
        },
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
        loop_to_save,
        {
            "source": "config",
            "target": "save",
            "data_mapping": [{"source_output": "config", "target_input": "config"}],
        },
    ]
    return {"graph": {"id": "workflow31"}, "nodes": nodes, "links": links}


@pytest.mark.parametrize("repeat", range(5))
def test_workflow31_required_link(ppf_log_config, repeat):
    """With an explicitly required link from "loop", "save" should only be
    triggered when both "loop" and "config" have provided their inputs."""
    _SAVED.clear()
    execute_graph(
        workflow31(required_loop_link=True),
        pool_type="thread",
        scaling_workers=False,
    )
    assert sorted(_SAVED) == list(range(1, 11))


@pytest.mark.xfail(
    strict=True,
    reason="the conditional self-link of 'loop' makes 'loop -> save' optional by default (issue #16)",
)
def test_workflow31_default_link_is_required():
    taskgraph = load_graph(workflow31(required_loop_link=False))
    assert analysis.link_is_required(taskgraph.graph, "loop", "save")


@pytest.mark.xfail(
    strict=True,
    reason="'save' is triggered by 'config' before 'loop' provides 'i' (issue #16)",
)
def test_workflow31_default_link(ppf_log_config):
    _SAVED.clear()
    execute_graph(
        workflow31(required_loop_link=False),
        pool_type="thread",
        scaling_workers=False,
    )
    assert sorted(_SAVED) == list(range(1, 11))
