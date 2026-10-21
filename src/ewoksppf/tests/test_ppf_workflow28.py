import threading
from collections import Counter

import pytest
from ewokscore.graph import analysis
from ewokscore.graph import load_graph
from ewoksutils.import_utils import qualname

from ewoksppf import execute_graph

_EXECUTED = Counter()
_LOCK = threading.Lock()


def _executed(name: str, a=None, b=None) -> dict:
    with _LOCK:
        _EXECUTED[name] += 1
    return {"a": (a or 0) + 1, "b": (b or 0) + 1}


def start0(**kw):
    return _executed("start0", **kw)


def start(**kw):
    return _executed("start", **kw)


def up(**kw):
    return _executed("up", **kw)


def down(**kw):
    return _executed("down", **kw)


def end(**kw):
    return _executed("end", **kw)


def workflow28():
    nodes = [
        {"id": "start0", "task_type": "ppfmethod", "task_identifier": qualname(start0)},
        {"id": "start", "task_type": "ppfmethod", "task_identifier": qualname(start)},
        {"id": "up", "task_type": "ppfmethod", "task_identifier": qualname(up)},
        {"id": "down", "task_type": "ppfmethod", "task_identifier": qualname(down)},
        {"id": "end", "task_type": "ppfmethod", "task_identifier": qualname(end)},
    ]
    links = [
        {
            "source": "start0",
            "target": "start",
            "map_all_data": True,
            "conditions": [{"source_output": "a", "value": 1}],
        },
        {"source": "start", "target": "up", "map_all_data": True},
        {"source": "start", "target": "down", "map_all_data": True},
        {"source": "up", "target": "end", "map_all_data": True},
        {"source": "down", "target": "end", "map_all_data": True},
    ]
    return {"graph": {"id": "workflow28"}, "links": links, "nodes": nodes}


def test_workflow28_required_links():
    """A conditional link upstream should not make the links of the
    unconditional branches downstream optional (issue #23)."""
    taskgraph = load_graph(workflow28())
    required = {
        (source, target): analysis.link_is_required(taskgraph.graph, source, target)
        for source, target in taskgraph.graph.edges
    }
    expected = {
        ("start0", "start"): False,
        ("start", "up"): True,
        ("start", "down"): True,
        ("up", "end"): True,
        ("down", "end"): True,
    }
    assert required == expected


@pytest.mark.parametrize("repeat", range(10))
def test_workflow28(ppf_log_config, repeat):
    """Each task should be executed exactly once (issue #23)."""
    _EXECUTED.clear()
    result = execute_graph(workflow28(), pool_type="thread")
    assert _EXECUTED == {"start0": 1, "start": 1, "up": 1, "down": 1, "end": 1}
    assert result == {"_ppfdict": {"a": 4, "b": 4}}
