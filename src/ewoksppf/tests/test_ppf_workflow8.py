from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


def submodel8():
    nodes = [
        {
            "id": "addtask2",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddB2C.run",
        }
    ]

    links = []

    graph = {
        "graph": {"id": "submodel8"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow8():
    nodes = [
        {
            "id": "addtask1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddA2B.run",
        },
        {
            "id": "addtask3",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddABC2D.run",
        },
        {"id": "submodel8", "task_type": "graph", "task_identifier": submodel8()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel8",
            "sub_target": "addtask2",
            "map_all_data": True,
        },
        {
            "source": "submodel8",
            "sub_source": "addtask2",
            "target": "addtask3",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow8"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"a": 1, "b": 2}},
        ("submodel8", "addtask2"): {"_ppfdict": {"a": 1, "b": 2, "c": 3}},
        "addtask3": {"_ppfdict": {"a": 1, "b": 2, "c": 3, "d": 6}},
    }

    return graph, expected_results


def test_workflow8(ppf_log_config, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow8()
    result = execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
