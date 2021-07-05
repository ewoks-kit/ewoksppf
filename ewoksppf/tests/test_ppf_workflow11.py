from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel11a():
    nodes = [
        {
            "id": "addtask2aa",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2ab",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "in11a", "ppfport": "input"},
        {"id": "out11a", "ppfport": "output"},
    ]

    links = [
        {"source": "in11a", "target": "addtask2aa", "all_arguments": True},
        {"source": "addtask2aa", "target": "addtask2ab", "all_arguments": True},
        {"source": "addtask2ab", "target": "out11a", "all_arguments": True},
    ]

    graph = {
        "directed": True,
        "graph": {"name": "submodel11a"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def submodel11b():
    nodes = [
        {
            "id": "addtask2ba",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2bb",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel11a", "graph": submodel11a()},
        {"id": "in11b", "ppfport": "input"},
        {"id": "out11b", "ppfport": "output"},
    ]

    links = [
        {"source": "in11b", "target": "addtask2ba", "all_arguments": True},
        {
            "source": "addtask2ba",
            "target": "submodel11a",
            "links": [
                {
                    "source": "addtask2ba",
                    "target": "in11a",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel11a",
            "target": "addtask2bb",
            "links": [
                {
                    "source": "out11a",
                    "target": "addtask2bb",
                    "all_arguments": True,
                }
            ],
        },
        {"source": "addtask2bb", "target": "out11b", "all_arguments": True},
    ]

    graph = {
        "directed": True,
        "graph": {"name": "submodel11b"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow11():
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"value": 1},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask3",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel11b", "graph": submodel11b()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel11b",
            "links": [
                {
                    "source": "addtask1",
                    "target": "in11b",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel11b",
            "target": "addtask3",
            "links": [
                {
                    "source": "out11b",
                    "target": "addtask3",
                    "all_arguments": True,
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow11"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"value": 2}},
        ("submodel11b", "in11b"): {"ppfdict": {"value": 2}},
        ("submodel11b", "addtask2ba"): {"ppfdict": {"value": 3}},
        ("submodel11b", ("submodel11a", "in11a")): {"ppfdict": {"value": 3}},
        ("submodel11b", ("submodel11a", "addtask2aa")): {"ppfdict": {"value": 4}},
        ("submodel11b", ("submodel11a", "addtask2ab")): {"ppfdict": {"value": 5}},
        ("submodel11b", ("submodel11a", "out11a")): {"ppfdict": {"value": 5}},
        ("submodel11b", "addtask2bb"): {"ppfdict": {"value": 6}},
        ("submodel11b", "out11b"): {"ppfdict": {"value": 6}},
        "addtask3": {"ppfdict": {"value": 7}},
    }

    return graph, expected_results


def test_workflow11(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow11()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
