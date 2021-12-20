from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_all_tasks


def submodel6():
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
        "graph": {"name": "submodel6"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow6():
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
        {"id": "submodel6", "task_type": "graph", "task_identifier": submodel6()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel6",
            "sub_target": "in",
            "map_all_data": True,
        },
        {
            "source": "submodel6",
            "sub_source": "out",
            "target": "addtask3",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow6"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"value": 2}},
        ("submodel6", "in"): {"_ppfdict": {"value": 2}},
        ("submodel6", "addtask2a"): {"_ppfdict": {"value": 3}},
        ("submodel6", "addtask2b"): {"_ppfdict": {"value": 4}},
        ("submodel6", "out"): {"_ppfdict": {"value": 4}},
        "addtask3": {"_ppfdict": {"value": 5}},
    }

    return graph, expected_results


def test_workflow6(ppf_log_config, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow6()
    execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_all_tasks(graph, expected, varinfo=varinfo)
