from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_all_tasks


def submodel14a():
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
        {"id": "In", "task_type": "ppfport"},
        {"id": "Out", "task_type": "ppfport"},
    ]

    links = [
        {"source": "In", "target": "addtask2aa", "map_all_data": True},
        {"source": "addtask2aa", "target": "addtask2ab", "map_all_data": True},
        {"source": "addtask2ab", "target": "Out", "map_all_data": True},
    ]

    graph = {
        "graph": {"name": "submodel14a"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def submodel14b():
    nodes = [
        {"id": "submodel14a", "task_type": "graph", "task_identifier": submodel14a()},
        {"id": "In", "task_type": "ppfport"},
        {"id": "Out", "task_type": "ppfport"},
    ]

    links = [
        {
            "source": "In",
            "target": "submodel14a",
            "sub_target": "In",
            "map_all_data": True,
        },
        {
            "source": "submodel14a",
            "sub_source": "Out",
            "target": "Out",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"name": "submodel14b"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow14():
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
        {"id": "submodel14b", "task_type": "graph", "task_identifier": submodel14b()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel14b",
            "sub_target": "In",
            "map_all_data": True,
        },
        {
            "source": "submodel14b",
            "sub_source": "Out",
            "target": "addtask3",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow14"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"value": 2}},
        ("submodel14b", "In"): {"_ppfdict": {"value": 2}},
        ("submodel14b", ("submodel14a", "In")): {"_ppfdict": {"value": 2}},
        ("submodel14b", ("submodel14a", "addtask2aa")): {"_ppfdict": {"value": 3}},
        ("submodel14b", ("submodel14a", "addtask2ab")): {"_ppfdict": {"value": 4}},
        ("submodel14b", ("submodel14a", "Out")): {"_ppfdict": {"value": 4}},
        ("submodel14b", "Out"): {"_ppfdict": {"value": 4}},
        "addtask3": {"_ppfdict": {"value": 5}},
    }

    return graph, expected_results


def test_workflow14(ppf_log_config, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow14()
    execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_all_tasks(graph, expected, varinfo=varinfo)
