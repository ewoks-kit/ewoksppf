from typing import Optional

import pytest
from ewokscore.bindings import execute_graph as execute_graph_sequential
from ewokscore.missing_data import MISSING_DATA
from ewokscore.task import Task
from ewoksutils.import_utils import qualname

from ..bindings import execute_graph

OUTPUT_CONFIGURATIONS = [
    None,
    [],
    [{"all": False}],
    [{"all": True}],
    [{"id": "task5"}],
    [{"label": "task5"}],
    [{"id": "task1", "name": "inputs"}, {"id": "task4", "name": "result"}],
    [{"id": "task1", "name": "inputs", "new_name": "a"}, {"id": "task4"}],
    [{"id": "task1", "name": "not_an_output"}],
    [{"id": "not_a_node"}],
]


@pytest.mark.parametrize("outputs", OUTPUT_CONFIGURATIONS)
@pytest.mark.parametrize("merge_outputs", [True, False], ids=["merge", "separate"])
def test_outputs_like_sequential(outputs, merge_outputs, ppf_log_config):
    """The Pypushflow engine returns the same outputs as the sequential engine."""
    expected = execute_graph_sequential(
        _create_graph(), outputs=outputs, merge_outputs=merge_outputs
    )
    result = execute_graph(
        _create_graph(), outputs=outputs, merge_outputs=merge_outputs
    )
    assert result == expected


def test_default_outputs(ppf_log_config):
    """The default is the merged outputs of the end nodes. The only end node
    of this graph has no outputs.
    """
    assert execute_graph(_create_graph()) == dict()


def test_all_outputs_merged(ppf_log_config):
    """'task6' is the last task with outputs so it takes precedence."""
    result = execute_graph(_create_graph(), outputs=[{"all": True}])
    assert result == {"inputs": {"a": 10, "b": 6}, "result": 16, "label": "task6"}


def test_all_outputs_per_task(ppf_log_config):
    result = execute_graph(
        _create_graph(), outputs=[{"all": True}], merge_outputs=False
    )
    assert result == {
        "task1": {"inputs": {"a": 1}, "result": 1, "label": "task1"},
        "task2": {"inputs": {"a": 2}, "result": 2, "label": "task2"},
        "task3": {"inputs": {"a": 1, "b": 3}, "result": 4, "label": "task3"},
        "task4": {"inputs": {"a": 2, "b": 4}, "result": 6, "label": "task4"},
        "task5": {"inputs": {"a": 4, "b": 6}, "result": 10, "label": "task5"},
        "task6": {"inputs": {"a": 10, "b": 6}, "result": 16, "label": "task6"},
        "task7": {},
    }


def test_selected_outputs_merged(ppf_log_config):
    result = execute_graph(
        _create_graph(),
        outputs=[
            {"id": "task1", "name": "inputs", "new_name": "a"},
            {"id": "task4", "name": "result"},
        ],
    )
    assert result == {"a": {"a": 1}, "result": 6}


def test_selected_outputs_per_task(ppf_log_config):
    result = execute_graph(
        _create_graph(),
        outputs=[
            {"id": "task1", "name": "inputs", "new_name": "a"},
            {"id": "task4", "name": "result"},
        ],
        merge_outputs=False,
    )
    assert result == {"task1": {"a": {"a": 1}}, "task4": {"result": 6}}


def test_missing_output(ppf_log_config):
    result = execute_graph(
        _create_graph(), outputs=[{"id": "task1", "name": "not_an_output"}]
    )
    assert result == {"not_an_output": MISSING_DATA}


def test_persistent_outputs(ppf_log_config, tmp_path):
    """Task outputs are passed around as URI's which need to be resolved."""
    varinfo = {"root_uri": str(tmp_path)}
    result = execute_graph(
        _create_graph(), outputs=[{"id": "task5"}], varinfo=varinfo, merge_outputs=False
    )
    assert result == {
        "task5": {"inputs": {"a": 4, "b": 6}, "result": 10, "label": "task5"}
    }


def test_sub_graph_outputs(ppf_log_config):
    """Nodes of sub-graphs are identified by a tuple of node id's."""
    result = execute_graph(
        _graph_with_sub_graph(),
        inputs=[{"name": "value", "value": 0}],
        outputs=[{"all": True}],
        merge_outputs=False,
    )
    assert result == {
        "task": {"return_value": 1},
        ("sub", "subtask1"): {"return_value": 2},
        ("sub", "subtask2"): {"return_value": 3},
    }

    result = execute_graph(
        _graph_with_sub_graph(), inputs=[{"name": "value", "value": 0}]
    )
    assert result == {"return_value": 3}


def _failing_graph() -> dict:
    return {
        "graph": {"id": "failing_graph"},
        "nodes": [
            {"id": "task", "task_type": "method", "task_identifier": qualname(add)},
            {"id": "failing", "task_type": "class", "task_identifier": qualname(Fail)},
        ],
        "links": [{"source": "task", "target": "failing", "map_all_data": True}],
    }


@pytest.mark.parametrize("merge_outputs", [True, False])
def test_error_without_raising(merge_outputs, ppf_log_config):
    """No outputs are returned when the workflow fails, even though the first
    task did finish successfully.
    """
    result = execute_graph(
        _failing_graph(),
        inputs=[{"name": "value", "value": 0}],
        outputs=[{"all": True}],
        merge_outputs=merge_outputs,
        raise_on_error=False,
    )
    assert result == dict()


@pytest.mark.parametrize("outputs", [None, [], [{"all": True}]])
@pytest.mark.parametrize("merge_outputs", [True, False])
def test_error_raised(outputs, merge_outputs, ppf_log_config):
    """The exception is raised whatever the requested outputs are."""
    with pytest.raises(RuntimeError, match="Intentional failure"):
        execute_graph(
            _failing_graph(),
            inputs=[{"name": "value", "value": 0}],
            outputs=outputs,
            merge_outputs=merge_outputs,
        )


@pytest.mark.parametrize("merge_outputs", [True, False])
def test_cyclic_graph_outputs(merge_outputs, ppf_log_config):
    """Only the result of the last execution of a task is returned."""
    result = execute_graph(
        _cyclic_graph(limit=5), outputs=[{"all": True}], merge_outputs=merge_outputs
    )
    expected = {"_ppfdict": {"value": 5, "limit": 5, "repeat": False}}
    if not merge_outputs:
        expected = {"loop": expected}
    assert result == expected


def add(value: Optional[int] = None, amount: int = 1) -> int:
    return value + amount


def add_until_limit(value: int = 0, limit: int = 1, **_) -> dict:
    value += 1
    return {"value": value, "repeat": value < limit}


class Fail(Task, optional_input_names=["return_value"]):
    def run(self):
        raise RuntimeError("Intentional failure")


class SumTask(
    Task,
    input_names=["a"],
    optional_input_names=["b"],
    output_names=["result", "inputs", "label"],
):
    def run(self):
        result = self.inputs.a
        if self.inputs.b:
            result += self.inputs.b
        self.outputs.result = result
        self.outputs.inputs = {k: v for k, v in self.get_input_values().items() if v}
        self.outputs.label = self.label


def _create_graph():
    task = qualname(SumTask)
    graph = {"id": "testgraph", "schema_version": "1.1"}
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task2",
            "default_inputs": [{"name": "a", "value": 2}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task3",
            "default_inputs": [{"name": "b", "value": 3}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task4",
            "default_inputs": [{"name": "b", "value": 4}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task5",
            "default_inputs": [{"name": "b", "value": 5}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task6",
            "default_inputs": [{"name": "b", "value": 6}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task7",
            "task_type": "class",
            "task_identifier": "ewokscore.tests.examples.tasks.nooutputtask.NoOutputTask",
        },
    ]

    links = [
        {
            "source": "task1",
            "target": "task3",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task2",
            "target": "task4",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task3",
            "target": "task5",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task4",
            "target": "task5",
            "data_mapping": [{"source_output": "result", "target_input": "b"}],
        },
        {
            "source": "task5",
            "target": "task6",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task6",
            "target": "task7",
        },
    ]

    return {"graph": graph, "links": links, "nodes": nodes}


def _cyclic_graph(limit: int) -> dict:
    return {
        "graph": {"id": "cyclic_graph"},
        "nodes": [
            {
                "id": "loop",
                "task_type": "ppfmethod",
                "task_identifier": qualname(add_until_limit),
                "default_inputs": [
                    {"name": "value", "value": 0},
                    {"name": "limit", "value": limit},
                ],
                "force_start_node": True,
            }
        ],
        "links": [
            {
                "source": "loop",
                "target": "loop",
                "map_all_data": True,
                "conditions": [{"source_output": "repeat", "value": True}],
            }
        ],
    }


def _graph_with_sub_graph() -> dict:
    return {
        "graph": {"id": "graph_with_subgraph"},
        "nodes": [
            {"id": "task", "task_type": "method", "task_identifier": qualname(add)},
            {"id": "sub", "task_type": "graph", "task_identifier": _sub_graph()},
        ],
        "links": [
            {
                "source": "task",
                "target": "sub",
                "sub_target": "subtask1",
                "data_mapping": [
                    {"source_output": "return_value", "target_input": "value"}
                ],
            }
        ],
    }


def _sub_graph() -> dict:
    return {
        "graph": {
            "id": "subgraph",
            "input_nodes": [{"id": "in", "node": "subtask1"}],
            "output_nodes": [{"id": "out", "node": "subtask2"}],
        },
        "nodes": [
            {
                "id": "subtask1",
                "task_type": "method",
                "task_identifier": qualname(add),
            },
            {
                "id": "subtask2",
                "task_type": "method",
                "task_identifier": qualname(add),
            },
        ],
        "links": [
            {
                "source": "subtask1",
                "target": "subtask2",
                "data_mapping": [
                    {"source_output": "return_value", "target_input": "value"}
                ],
            }
        ],
    }
