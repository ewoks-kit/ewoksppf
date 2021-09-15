from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def workflow2():
    nodes = [
        {
            "id": "Python Error Handler Test",
            "default_inputs": [{"name": "name", "value": "myname"}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonErrorHandlerTest.run",
        },
    ]

    links = []

    graph = {
        "graph": {"name": "workflow2"},
        "links": links,
        "nodes": nodes,
    }

    # Eplicit check that the task didn't finish successfully
    expected_results = {"Python Error Handler Test": None}

    return graph, expected_results


def test_workflow2(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow2()
    result = execute_graph(graph, varinfo=varinfo, raise_on_error=False)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
    err_msg = "Runtime error in pythonErrorHandlerTest.py!"
    assert result["WorkflowException"]["errorMessage"] == err_msg
