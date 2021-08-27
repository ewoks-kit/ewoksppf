import pytest
from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def workflow18(dotask4=True):
    ppfmethod = "ewoksppf.tests.test_ppf_actors.pythonActorAddWithoutSleep.run"
    nodes = [
        {
            "id": "task1",
            "task_type": "ppfmethod",
            "task_identifier": ppfmethod,
            "inputs": {"value": 0},
        },
        {
            "id": "task2",
            "task_type": "ppfmethod",
            "task_identifier": ppfmethod,
            "inputs": {"value": 10},
        },
        {"id": "task3", "task_type": "ppfmethod", "task_identifier": ppfmethod},
        {"id": "task4", "task_type": "ppfmethod", "task_identifier": ppfmethod},
    ]
    links = [
        {"source": "task1", "target": "task3", "all_arguments": True},
        {"source": "task2", "target": "task3"},
        {
            "source": "task2",
            "target": "task4",
            "all_arguments": True,
            "conditions": {"value": 11 if dotask4 else 0},
        },
    ]
    graph = {
        "graph": {"name": "workflow18"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "task1": {"ppfdict": {"value": 1}},
        "task2": {"ppfdict": {"value": 11}},
        "task3": {"ppfdict": {"value": 2}},
    }

    if dotask4:
        expected_results["task4"] = {"ppfdict": {"value": 12}}
    else:
        expected_results["task4"] = None

    return graph, expected_results


@pytest.mark.parametrize("dotask4", [True, False])
def test_workflow18(dotask4, ppf_logging, tmpdir):
    """Test conditional links"""
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow18(dotask4=dotask4)
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
