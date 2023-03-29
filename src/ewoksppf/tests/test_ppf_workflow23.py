import pytest
from ewoksppf import execute_graph
from ewoksutils.import_utils import qualname
from ewokscore.tests.utils.results import assert_execute_graph_default_result


def raise_not_greater_than(**kwargs):
    name = kwargs.get("variable", None)
    if name in kwargs:
        assert kwargs[name] > kwargs["limit"]
    return kwargs


def work(**kwargs):
    tasks = kwargs["tasks"]
    groups = kwargs["groups"]
    new_tasks = list()
    for name in ["a", "b", "c"]:
        if kwargs.get(name) and name not in tasks:
            tasks.add(name)
            new_tasks.append(name)
    groups.add(tuple(new_tasks))
    return kwargs


def passthrough(**kwargs):
    return kwargs


def workflow():
    nodes = [
        {
            "id": "in",
            "task_type": "ppfmethod",
            "task_identifier": qualname(passthrough),
        },
        {
            "id": "out",
            "task_type": "ppfmethod",
            "task_identifier": qualname(passthrough),
        },
        {
            "id": "gt",
            "task_type": "ppfmethod",
            "task_identifier": qualname(raise_not_greater_than),
            "default_inputs": [{"name": "variable", "value": "value"}],
        },
        {
            "id": "worka",
            "task_type": "ppfmethod",
            "task_identifier": qualname(work),
            "default_inputs": [{"name": "a", "value": True}],
        },
        {
            "id": "workb",
            "task_type": "ppfmethod",
            "task_identifier": qualname(work),
            "default_inputs": [{"name": "b", "value": True}],
        },
        {
            "id": "workc",
            "task_type": "ppfmethod",
            "task_identifier": qualname(work),
            "default_inputs": [{"name": "c", "value": True}],
        },
    ]
    links = [
        {"source": "in", "target": "gt", "map_all_data": True},
        {"source": "gt", "target": "worka", "map_all_data": True},
        {"source": "gt", "target": "workb", "map_all_data": True},
        {"source": "gt", "target": "workc", "map_all_data": True, "on_error": True},
        {"source": "worka", "target": "out", "map_all_data": True},
        {"source": "workb", "target": "out", "map_all_data": True},
        {"source": "workc", "target": "out", "map_all_data": True},
    ]

    graph = {"links": links, "nodes": nodes}

    return graph


@pytest.mark.skip("Conditional branches that merge again are not handled yet")
@pytest.mark.parametrize("on_error", [True, False])
def test_ppf_workflow23(on_error, ppf_log_config, tmpdir):
    """Test error conditions."""

    graph = workflow()
    if on_error:
        expected = {"tasks": {"c"}, "groups": ({"c"},)}
    else:
        expected = {"tasks": {"a", "b"}, "groups": ({"a", "b"},)}
    inputs = [
        {"name": "limit", "value": 10},
        {"name": "value", "value": 0 if on_error else 20},
        {"name": "tasks", "value": set()},
        {"name": "groups", "value": set()},
    ]
    varinfo = {"root_uri": str(tmpdir)}
    result = execute_graph(graph, inputs=inputs, varinfo=varinfo)
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
