import pytest
from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


def submodel13():
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
        "graph": {"id": "submodel13"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow13(startvalue, withlastnode_startvalue):
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
        {"id": "submodel13", "task_type": "graph", "task_identifier": submodel13()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel13",
            "sub_target": "in",
            "map_all_data": True,
        },
        {
            "source": "submodel13",
            "sub_source": "out",
            "target": "addtask2",
            "map_all_data": True,
            "conditions": [
                {"source_output": "value", "value": withlastnode_startvalue + 3}
            ],
        },
    ]

    graph = {
        "graph": {"id": "workflow13"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"value": startvalue + 1}},
        ("submodel13", "in"): {"_ppfdict": {"value": startvalue + 1}},
        ("submodel13", "addtask2a"): {"_ppfdict": {"value": startvalue + 2}},
        ("submodel13", "addtask2b"): {"_ppfdict": {"value": startvalue + 3}},
        ("submodel13", "out"): {"_ppfdict": {"value": startvalue + 3}},
    }
    if startvalue == withlastnode_startvalue:
        expected_results["addtask2"] = {"_ppfdict": {"value": startvalue + 4}}

    return graph, expected_results


@pytest.mark.parametrize("startvalue", [0, 1])
def test_workflow13(startvalue, ppf_log_config, tmpdir):
    withlastnode_startvalue = 1
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow13(startvalue, withlastnode_startvalue)
    result = execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
