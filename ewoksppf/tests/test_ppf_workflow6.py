from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def submodel6():
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
        "graph": {"name": "submodel6"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow6():
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"value": 1},
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask3",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel6", "task_type": "graph", "task_identifier": submodel6()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel6",
            "all_arguments": True,
            "sub_graph_nodes": {
                "sub_target": "in",
            },
        },
        {
            "source": "submodel6",
            "target": "addtask3",
            "all_arguments": True,
            "sub_graph_nodes": {
                "sub_source": "out",
            },
        },
    ]

    graph = {
        "graph": {"name": "workflow6"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"value": 2}},
        ("submodel6", "in"): {"ppfdict": {"value": 2}},
        ("submodel6", "addtask2a"): {"ppfdict": {"value": 3}},
        ("submodel6", "addtask2b"): {"ppfdict": {"value": 4}},
        ("submodel6", "out"): {"ppfdict": {"value": 4}},
        "addtask3": {"ppfdict": {"value": 5}},
    }

    return graph, expected_results


def test_workflow6(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow6()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
