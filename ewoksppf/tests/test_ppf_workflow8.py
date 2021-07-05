from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel8():
    nodes = [
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAddB2C.run",
        }
    ]

    links = []

    graph = {
        "directed": True,
        "graph": {"name": "submodel8"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow8():
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"a": 1},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAddA2B.run",
        },
        {
            "id": "addtask3",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAddABC2D.run",
        },
        {"id": "submodel8", "graph": submodel8()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel8",
            "links": [
                {
                    "source": "addtask1",
                    "target": "addtask2",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel8",
            "target": "addtask3",
            "links": [
                {
                    "source": "addtask2",
                    "target": "addtask3",
                    "all_arguments": True,
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow8"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"a": 1, "b": 2}},
        ("submodel8", "addtask2"): {"ppfdict": {"a": 1, "b": 2, "c": 3}},
        "addtask3": {"ppfdict": {"a": 1, "b": 2, "c": 3, "d": 6}},
    }

    return graph, expected_results


def test_workflow8(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow8()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
