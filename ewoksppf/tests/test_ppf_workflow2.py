from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def workflow2():
    nodes = [
        {
            "id": "Python Error Handler Test",
            "inputs": {"name": "myname"},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonErrorHandlerTest.run",
        },
    ]

    links = []

    graph = {
        "directed": True,
        "graph": {"name": "workflow2"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    # Eplicit check that the task didn't finish successfully
    expected_results = {"Python Error Handler Test": None}

    return graph, expected_results


def test_workflow2(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow2()
    result = job(graph, varinfo=varinfo, raise_on_error=False)
    assert_taskgraph_result(graph, expected, varinfo)
    err_msg = "Runtime error in pythonErrorHandlerTest.py!"
    assert result["WorkflowException"]["errorMessage"] == err_msg
