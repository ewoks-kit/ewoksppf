from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def submodel1():
    nodes = [
        {
            "id": "mytask",
            "inputs": {"name": "myname"},
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
    ]

    links = []

    graph = {
        "graph": {"name": "submodel1"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow3():
    nodes = [
        {
            "id": "first",
            "inputs": {"name": "first"},
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
        {
            "id": "last",
            "inputs": {"name": "last"},
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
        {"id": "middle", "task_type": "graph", "task_identifier": submodel1()},
    ]

    links = [
        {
            "source": "first",
            "target": "middle",
            "sub_target_attributes": {"inputs": {"name": "middle"}},
            "sub_graph_nodes": {
                "sub_target": "mytask",
            },
        },
        {
            "source": "middle",
            "target": "last",
            "sub_graph_nodes": {
                "sub_source": "mytask",
            },
        },
    ]

    graph = {
        "graph": {"name": "workflow3"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "first": {"ppfdict": {"name": "first", "reply": "Hello first!"}},
        ("middle", "mytask"): {"ppfdict": {"name": "middle", "reply": "Hello middle!"}},
        "last": {"ppfdict": {"name": "last", "reply": "Hello last!"}},
    }

    return graph, expected_results


def test_workflow3(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow3()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
