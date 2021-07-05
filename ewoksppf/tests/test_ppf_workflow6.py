from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel6():
    nodes = [
        {
            "id": "addtask2a",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2b",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "in", "ppfport": "input"},
        {"id": "out", "ppfport": "output"},
    ]

    links = [
        {"source": "in", "target": "addtask2a", "all_arguments": True},
        {"source": "addtask2a", "target": "addtask2b", "all_arguments": True},
        {"source": "addtask2b", "target": "out", "all_arguments": True},
    ]

    graph = {
        "directed": True,
        "graph": {"name": "submodel6"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow6():
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
        {"id": "submodel6", "graph": submodel6()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel6",
            "links": [
                {
                    "source": "addtask1",
                    "target": "in",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel6",
            "target": "addtask3",
            "links": [
                {
                    "source": "out",
                    "target": "addtask3",
                    "all_arguments": True,
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow6"},
        "links": links,
        "multigraph": False,
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
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
