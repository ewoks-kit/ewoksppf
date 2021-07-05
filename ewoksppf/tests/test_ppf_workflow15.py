from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel15(name):
    nodes = [
        {
            "id": "addtask1",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "in", "ppfport": "input"},
        {"id": "out", "ppfport": "output"},
    ]

    links = [
        {"source": "in", "target": "addtask1", "all_arguments": True},
        {"source": "addtask1", "target": "addtask2", "all_arguments": True},
        {"source": "addtask2", "target": "out", "all_arguments": True},
    ]

    graph = {
        "directed": True,
        "graph": {"name": name},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow15():
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"value": 1},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel15a", "graph": submodel15("submodel15a")},
        {"id": "submodel15b", "graph": submodel15("submodel15b")},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel15a",
            "links": [
                {
                    "source": "addtask1",
                    "target": "in",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel15a",
            "target": "submodel15b",
            "links": [
                {
                    "source": "out",
                    "target": "in",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel15b",
            "target": "addtask2",
            "links": [
                {
                    "source": "out",
                    "target": "addtask2",
                    "all_arguments": True,
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow15"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"value": 2}},
        ("submodel15a", "in"): {"ppfdict": {"value": 2}},
        ("submodel15a", "addtask1"): {"ppfdict": {"value": 3}},
        ("submodel15a", "addtask2"): {"ppfdict": {"value": 4}},
        ("submodel15a", "out"): {"ppfdict": {"value": 4}},
        ("submodel15b", "in"): {"ppfdict": {"value": 4}},
        ("submodel15b", "addtask1"): {"ppfdict": {"value": 5}},
        ("submodel15b", "addtask2"): {"ppfdict": {"value": 6}},
        ("submodel15b", "out"): {"ppfdict": {"value": 6}},
        "addtask2": {"ppfdict": {"value": 7}},
    }

    return graph, expected_results


def test_workflow15(ppf_logging, tmpdir):
    """Test connecting nodes from submodels directly"""
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow15()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
