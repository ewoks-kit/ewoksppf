import pytest
from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel13():
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
        "graph": {"name": "submodel13"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow13(startvalue, withlastnode_startvalue):
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"value": startvalue},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel13", "graph": submodel13()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel13",
            "links": [
                {
                    "source": "addtask1",
                    "target": "in",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel13",
            "target": "addtask2",
            "links": [
                {
                    "source": "out",
                    "target": "addtask2",
                    "all_arguments": True,
                    "conditions": {"value": withlastnode_startvalue + 3},
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow13"},
        "links": links,
        "multigraph": False,
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
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
