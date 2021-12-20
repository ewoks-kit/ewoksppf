from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_all_tasks


def submodel7():
    nodes = [
        {
            "id": "addtask2",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd2.run",
        },
    ]

    links = []

    graph = {
        "graph": {"name": "submodel7"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow7():
    nodes = [
        {
            "id": "addtask1",
            "default_inputs": [{"name": "all_arguments", "value": {"value": 1}}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd2.run",
        },
        {
            "id": "addtask3",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd2.run",
        },
        {"id": "submodel7", "task_type": "graph", "task_identifier": submodel7()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel7",
            "sub_target": "addtask2",
            "map_all_data": True,
        },
        {
            "source": "submodel7",
            "sub_source": "addtask2",
            "target": "addtask3",
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow7"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"_ppfdict": {"all_arguments": {"value": 2}}},
        ("submodel7", "addtask2"): {"_ppfdict": {"all_arguments": {"value": 3}}},
        "addtask3": {"_ppfdict": {"all_arguments": {"value": 4}}},
    }

    return graph, expected_results


def test_workflow7(ppf_log_config, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow7()
    execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_all_tasks(graph, expected, varinfo=varinfo)
