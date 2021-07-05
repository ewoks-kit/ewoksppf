import pytest
from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel12():
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
        "graph": {"name": "submodel12"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow12(startvalue, withsubmodel_startvalue):
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
        {"id": "submodel12", "graph": submodel12()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel12",
            "links": [
                {
                    "source": "addtask1",
                    "target": "in",
                    "all_arguments": True,
                    "conditions": {"value": withsubmodel_startvalue + 1},
                }
            ],
        },
        {
            "source": "submodel12",
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
        "graph": {"name": "workflow12"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    value = startvalue
    value += 1
    expected_results = {"addtask1": {"ppfdict": {"value": value}}}
    if startvalue == withsubmodel_startvalue:
        expected_results[("submodel12", "in")] = {"ppfdict": {"value": value}}
        value += 1
        expected_results[("submodel12", "addtask2a")] = {"ppfdict": {"value": value}}
        value += 1
        expected_results[("submodel12", "addtask2b")] = {"ppfdict": {"value": value}}
        expected_results[("submodel12", "out")] = {"ppfdict": {"value": value}}
        value += 1
        expected_results["addtask2"] = {"ppfdict": {"value": value}}

    return graph, expected_results


@pytest.mark.parametrize("startvalue", [0, 1])
def test_workflow12(startvalue, ppf_logging, tmpdir):
    withsubmodel_startvalue = 1
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow12(startvalue, withsubmodel_startvalue)
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
