from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


def submodel16a():
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
        "graph": {"id": "submodel16a"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def submodel16b():
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
        {"id": "submodel16a", "task_type": "graph", "task_identifier": submodel16a()},
        {"id": "in", "task_type": "ppfport"},
        {"id": "out", "task_type": "ppfport"},
    ]

    links = [
        {"source": "in", "target": "addtask1", "map_all_data": True},
        {
            "source": "addtask1",
            "target": "submodel16a",
            "sub_target": "in",
            "map_all_data": True,
        },
        {
            "source": "submodel16a",
            "sub_source": "out",
            "target": "addtask2",
            "map_all_data": True,
        },
        {"source": "addtask2", "target": "out", "map_all_data": True},
    ]

    graph = {
        "graph": {"id": "submodel16b"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow16():
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
        {"id": "submodel16b", "task_type": "graph", "task_identifier": submodel16b()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel16b",
            "sub_target": "in",
            "map_all_data": True,
        },
        {
            "source": "submodel16b",
            "sub_source": ("submodel16a", "out"),
            "target": "addtask2",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow16"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"value": 2}},
        ("submodel16b", "in"): {"_ppfdict": {"value": 2}},
        ("submodel16b", "addtask1"): {"_ppfdict": {"value": 3}},
        ("submodel16b", ("submodel16a", "in")): {"_ppfdict": {"value": 3}},
        ("submodel16b", ("submodel16a", "addtask1")): {"_ppfdict": {"value": 4}},
        ("submodel16b", ("submodel16a", "addtask2")): {"_ppfdict": {"value": 5}},
        ("submodel16b", ("submodel16a", "out")): {
            "_ppfdict": {"value": 5}
        },  # 2 destinations
        ("submodel16b", "addtask2"): {"_ppfdict": {"value": 6}},
        ("submodel16b", "out"): {"_ppfdict": {"value": 6}},
        "addtask2": {"_ppfdict": {"value": 6}},
    }

    return graph, expected_results


def test_workflow16(ppf_log_config, tmpdir):
    """Test connecting nodes from sub-submodels to the top model"""
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow16()
    result = execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
