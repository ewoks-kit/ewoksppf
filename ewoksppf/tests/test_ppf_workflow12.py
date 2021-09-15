import pytest
from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def submodel12():
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
        {"source": "in", "target": "addtask2a", "map_all_data": True},
        {"source": "addtask2a", "target": "addtask2b", "map_all_data": True},
        {"source": "addtask2b", "target": "out", "map_all_data": True},
    ]

    graph = {
        "graph": {"name": "submodel12"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow12(startvalue, withsubmodel_startvalue):
    nodes = [
        {
            "id": "addtask1",
            "default_inputs": [{"name": "value", "value": startvalue}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel12", "task_type": "graph", "task_identifier": submodel12()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel12",
            "sub_target": "in",
            "map_all_data": True,
            "conditions": [
                {"source_output": "value", "value": withsubmodel_startvalue + 1}
            ],
        },
        {
            "source": "submodel12",
            "sub_source": "out",
            "target": "addtask2",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"name": "workflow12"},
        "links": links,
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
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
