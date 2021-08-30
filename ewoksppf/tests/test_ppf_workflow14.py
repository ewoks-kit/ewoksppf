from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def submodel14a():
    nodes = [
        {
            "id": "addtask2aa",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2ab",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "In", "task_type": "ppfport"},
        {"id": "Out", "task_type": "ppfport"},
    ]

    links = [
        {"source": "In", "target": "addtask2aa", "all_arguments": True},
        {"source": "addtask2aa", "target": "addtask2ab", "all_arguments": True},
        {"source": "addtask2ab", "target": "Out", "all_arguments": True},
    ]

    graph = {
        "directed": True,
        "graph": {"name": "submodel14a"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def submodel14b():
    nodes = [
        {"id": "submodel14a", "task_type": "graph", "task_identifier": submodel14a()},
        {"id": "In", "task_type": "ppfport"},
        {"id": "Out", "task_type": "ppfport"},
    ]

    links = [
        {
            "source": "In",
            "target": "submodel14a",
            "links": [
                {
                    "source": "In",
                    "target": "In",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel14a",
            "target": "Out",
            "links": [
                {
                    "source": "Out",
                    "target": "Out",
                    "all_arguments": True,
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "submodel14b"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow14():
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
        {"id": "submodel14b", "task_type": "graph", "task_identifier": submodel14b()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel14b",
            "links": [
                {
                    "source": "addtask1",
                    "target": "In",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel14b",
            "target": "addtask3",
            "links": [
                {
                    "source": "Out",
                    "target": "addtask3",
                    "all_arguments": True,
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow14"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"value": 2}},
        ("submodel14b", "In"): {"ppfdict": {"value": 2}},
        ("submodel14b", ("submodel14a", "In")): {"ppfdict": {"value": 2}},
        ("submodel14b", ("submodel14a", "addtask2aa")): {"ppfdict": {"value": 3}},
        ("submodel14b", ("submodel14a", "addtask2ab")): {"ppfdict": {"value": 4}},
        ("submodel14b", ("submodel14a", "Out")): {"ppfdict": {"value": 4}},
        ("submodel14b", "Out"): {"ppfdict": {"value": 4}},
        "addtask3": {"ppfdict": {"value": 5}},
    }

    return graph, expected_results


def test_workflow14(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow14()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
