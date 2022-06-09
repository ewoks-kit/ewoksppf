from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


def submodel15(name):
    nodes = [
        {
            "id": "addtask1",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "in", "task_type": "ppfport"},
        {"id": "out", "task_type": "ppfport"},
    ]

    links = [
        {"source": "in", "target": "addtask1", "map_all_data": True},
        {"source": "addtask1", "target": "addtask2", "map_all_data": True},
        {"source": "addtask2", "target": "out", "map_all_data": True},
    ]

    graph = {
        "graph": {"id": name},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow15():
    nodes = [
        {
            "id": "addtask1",
            "default_inputs": [{"name": "value", "value": 1}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "submodel15a",
            "task_type": "graph",
            "task_identifier": submodel15("submodel15a"),
        },
        {
            "id": "submodel15b",
            "task_type": "graph",
            "task_identifier": submodel15("submodel15b"),
        },
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel15a",
            "sub_target": "in",
            "map_all_data": True,
        },
        {
            "source": "submodel15a",
            "sub_source": "out",
            "target": "submodel15b",
            "sub_target": "in",
            "map_all_data": True,
        },
        {
            "source": "submodel15b",
            "sub_source": "out",
            "target": "addtask2",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow15"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"value": 2}},
        ("submodel15a", "in"): {"_ppfdict": {"value": 2}},
        ("submodel15a", "addtask1"): {"_ppfdict": {"value": 3}},
        ("submodel15a", "addtask2"): {"_ppfdict": {"value": 4}},
        ("submodel15a", "out"): {"_ppfdict": {"value": 4}},
        ("submodel15b", "in"): {"_ppfdict": {"value": 4}},
        ("submodel15b", "addtask1"): {"_ppfdict": {"value": 5}},
        ("submodel15b", "addtask2"): {"_ppfdict": {"value": 6}},
        ("submodel15b", "out"): {"_ppfdict": {"value": 6}},
        "addtask2": {"_ppfdict": {"value": 7}},
    }

    return graph, expected_results


def test_workflow15(ppf_log_config, tmpdir):
    """Test connecting nodes from submodels directly"""
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow15()
    result = execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
