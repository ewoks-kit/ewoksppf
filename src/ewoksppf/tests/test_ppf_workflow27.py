import threading
from collections import Counter

import pytest
from ewokscore.graph import analysis
from ewokscore.graph import load_graph
from ewoksutils.import_utils import qualname

from ewoksppf import execute_graph

_EXECUTED = Counter()
_LOCK = threading.Lock()


def _executed(name: str) -> dict:
    with _LOCK:
        _EXECUTED[name] += 1
    return {}


def locate_data(raise_error=False, **_):
    if raise_error:
        raise RuntimeError("raise in locate_data")
    return _executed("locate_data")


def terminate(**_):
    return _executed("terminate")


def setup_workdir(**_):
    return _executed("setup_workdir")


def load_master(**_):
    return _executed("load_master")


def load_metadata(**_):
    return _executed("load_metadata")


def draw_plots(**_):
    return _executed("draw_plots")


def workflow27(raise_error: bool):
    nodes = [
        {
            "id": "locate_data",
            "force_start_node": True,
            "default_inputs": [{"name": "raise_error", "value": raise_error}],
            "task_type": "ppfmethod",
            "task_identifier": qualname(locate_data),
        },
        {
            "id": "terminate",
            "task_type": "ppfmethod",
            "task_identifier": qualname(terminate),
        },
        {
            "id": "setup_workdir",
            "task_type": "ppfmethod",
            "task_identifier": qualname(setup_workdir),
        },
        {
            "id": "load_master",
            "task_type": "ppfmethod",
            "task_identifier": qualname(load_master),
        },
        {
            "id": "load_metadata",
            "task_type": "ppfmethod",
            "task_identifier": qualname(load_metadata),
        },
        {
            "id": "draw_plots",
            "task_type": "ppfmethod",
            "task_identifier": qualname(draw_plots),
        },
    ]
    links = [
        {"source": "locate_data", "target": "terminate", "on_error": True},
        {"source": "locate_data", "target": "setup_workdir"},
        {"source": "locate_data", "target": "load_master"},
        {"source": "locate_data", "target": "load_metadata"},
        {"source": "setup_workdir", "target": "load_master"},
        {"source": "setup_workdir", "target": "load_metadata"},
        {"source": "load_master", "target": "draw_plots"},
        {"source": "load_metadata", "target": "draw_plots"},
    ]
    return {"graph": {"id": "workflow27"}, "links": links, "nodes": nodes}


def test_workflow27_required_links():
    """An error handler on a node should not make the links of its
    regular downstream branches optional (issue #159)."""
    taskgraph = load_graph(workflow27(raise_error=False))
    required = {
        (source, target): analysis.link_is_required(taskgraph.graph, source, target)
        for source, target in taskgraph.graph.edges
    }
    expected = {
        ("locate_data", "terminate"): False,
        ("locate_data", "setup_workdir"): True,
        ("locate_data", "load_master"): True,
        ("locate_data", "load_metadata"): True,
        ("setup_workdir", "load_master"): True,
        ("setup_workdir", "load_metadata"): True,
        ("load_master", "draw_plots"): True,
        ("load_metadata", "draw_plots"): True,
    }
    assert required == expected


@pytest.mark.parametrize("repeat", range(10))
def test_workflow27_no_error(ppf_log_config, repeat):
    """Each task should be executed exactly once (issue #159)."""
    _EXECUTED.clear()
    execute_graph(workflow27(raise_error=False), pool_type="thread")
    assert _EXECUTED == {
        "locate_data": 1,
        "setup_workdir": 1,
        "load_master": 1,
        "load_metadata": 1,
        "draw_plots": 1,
    }


def test_workflow27_error(ppf_log_config):
    """Only the error handler should be executed after the first task fails."""
    _EXECUTED.clear()
    execute_graph(workflow27(raise_error=True), pool_type="thread")
    assert _EXECUTED == {"terminate": 1}
