from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


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
            "inputs": {"all_arguments": {"value": 1}},
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
            "all_arguments": True,
            "sub_graph_nodes": {
                "sub_target": "addtask2",
            },
        },
        {
            "source": "submodel7",
            "target": "addtask3",
            "all_arguments": True,
            "sub_graph_nodes": {
                "sub_source": "addtask2",
            },
        },
    ]

    graph = {
        "graph": {"name": "workflow7"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"all_arguments": {"value": 2}}},
        ("submodel7", "addtask2"): {"ppfdict": {"all_arguments": {"value": 3}}},
        "addtask3": {"ppfdict": {"all_arguments": {"value": 4}}},
    }

    return graph, expected_results


def test_workflow7(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow7()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
