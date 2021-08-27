import pytest
from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def submodel13():
    nodes = [
        {
            "id": "addtask2a",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2b",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "in", "task_type": "ppfport"},
        {"id": "out", "task_type": "ppfport"},
    ]

    links = [
        {"source": "in", "target": "addtask2a", "all_arguments": True},
        {"source": "addtask2a", "target": "addtask2b", "all_arguments": True},
        {"source": "addtask2b", "target": "out", "all_arguments": True},
    ]

    graph = {
        "graph": {"name": "submodel13"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow13(startvalue, withlastnode_startvalue):
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"value": startvalue},
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel13", "task_type": "graph", "task_identifier": submodel13()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel13",
            "all_arguments": True,
            "sub_graph_nodes": {
                "sub_target": "in",
            },
        },
        {
            "source": "submodel13",
            "target": "addtask2",
            "all_arguments": True,
            "conditions": {"value": withlastnode_startvalue + 3},
            "sub_graph_nodes": {
                "sub_source": "out",
            },
        },
    ]

    graph = {
        "graph": {"name": "workflow13"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"value": startvalue + 1}},
        ("submodel13", "in"): {"ppfdict": {"value": startvalue + 1}},
        ("submodel13", "addtask2a"): {"ppfdict": {"value": startvalue + 2}},
        ("submodel13", "addtask2b"): {"ppfdict": {"value": startvalue + 3}},
        ("submodel13", "out"): {"ppfdict": {"value": startvalue + 3}},
    }
    if startvalue == withlastnode_startvalue:
        expected_results["addtask2"] = {"ppfdict": {"value": startvalue + 4}}

    return graph, expected_results


@pytest.mark.parametrize("startvalue", [0, 1])
def test_workflow13(startvalue, ppf_logging, tmpdir):
    withlastnode_startvalue = 1
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow13(startvalue, withlastnode_startvalue)
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
