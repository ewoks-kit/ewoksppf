from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel7():
    nodes = [
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd2.run",
        },
    ]

    links = []

    graph = {
        "directed": True,
        "graph": {"name": "submodel7"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow7():
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"all_arguments": {"value": 1}},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd2.run",
        },
        {
            "id": "addtask3",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd2.run",
        },
        {"id": "submodel7", "graph": submodel7()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel7",
            "links": [
                {
                    "source": "addtask1",
                    "target": "addtask2",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel7",
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
        "graph": {"name": "workflow7"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"all_arguments": {"value": 2}}},
        ("submodel7", "addtask2"): {"ppfdict": {"all_arguments": {"value": 3}}},
        "addtask3": {"ppfdict": {"all_arguments": {"value": 4}}},
    }

    return graph, expected_results


def test_workflow7(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow7()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
