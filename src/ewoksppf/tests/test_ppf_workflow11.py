from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


def submodel11a():
    nodes = [
        {
            "id": "addtask2aa",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2ab",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "in11a", "task_type": "ppfport"},
        {"id": "out11a", "task_type": "ppfport"},
    ]

    links = [
        {"source": "in11a", "target": "addtask2aa", "map_all_data": True},
        {"source": "addtask2aa", "target": "addtask2ab", "map_all_data": True},
        {"source": "addtask2ab", "target": "out11a", "map_all_data": True},
    ]

    graph = {
        "graph": {"id": "submodel11a"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def submodel11b():
    nodes = [
        {
            "id": "addtask2ba",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2bb",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel11a", "task_type": "graph", "task_identifier": submodel11a()},
        {"id": "in11b", "task_type": "ppfport"},
        {"id": "out11b", "task_type": "ppfport"},
    ]

    links = [
        {"source": "in11b", "target": "addtask2ba", "map_all_data": True},
        {
            "source": "addtask2ba",
            "target": "submodel11a",
            "sub_target": "in11a",
            "map_all_data": True,
        },
        {
            "source": "submodel11a",
            "sub_source": "out11a",
            "target": "addtask2bb",
            "map_all_data": True,
        },
        {"source": "addtask2bb", "target": "out11b", "map_all_data": True},
    ]

    graph = {
        "graph": {"id": "submodel11b"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow11():
    nodes = [
        {
            "id": "addtask1",
            "default_inputs": [{"name": "value", "value": 1}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask3",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel11b", "task_type": "graph", "task_identifier": submodel11b()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel11b",
            "sub_target": "in11b",
            "map_all_data": True,
        },
        {
            "source": "submodel11b",
            "sub_source": "out11b",
            "target": "addtask3",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow11"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"value": 2}},
        ("submodel11b", "in11b"): {"_ppfdict": {"value": 2}},
        ("submodel11b", "addtask2ba"): {"_ppfdict": {"value": 3}},
        ("submodel11b", ("submodel11a", "in11a")): {"_ppfdict": {"value": 3}},
        ("submodel11b", ("submodel11a", "addtask2aa")): {"_ppfdict": {"value": 4}},
        ("submodel11b", ("submodel11a", "addtask2ab")): {"_ppfdict": {"value": 5}},
        ("submodel11b", ("submodel11a", "out11a")): {"_ppfdict": {"value": 5}},
        ("submodel11b", "addtask2bb"): {"_ppfdict": {"value": 6}},
        ("submodel11b", "out11b"): {"_ppfdict": {"value": 6}},
        "addtask3": {"_ppfdict": {"value": 7}},
    }

    return graph, expected_results


def test_workflow11(ppf_log_config, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow11()
    result = execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
