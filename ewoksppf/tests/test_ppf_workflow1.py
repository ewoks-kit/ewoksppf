from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def workflow1():
    nodes = [
        {
            "id": "Python Actor Test",
            "inputs": {"name": "myname"},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
    ]

    links = []

    graph = {
        "directed": True,
        "graph": {"name": "workflow1"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "Python Actor Test": {"ppfdict": {"name": "myname", "reply": "Hello myname!"}}
    }

    return graph, expected_results


def test_workflow1(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow1()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
