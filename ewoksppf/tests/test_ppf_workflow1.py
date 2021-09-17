from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def workflow1():
    nodes = [
        {
            "id": "Python Actor Test",
            "default_inputs": [{"name": "name", "value": "myname"}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
    ]

    links = []

    graph = {
        "graph": {"name": "workflow1"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "Python Actor Test": {"ppfdict": {"name": "myname", "reply": "Hello myname!"}}
    }

    return graph, expected_results


def test_workflow1(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow1()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
