import pytest
from ewokscore.tests.utils.results import assert_execute_graph_default_result

from ewoksppf import execute_graph


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
        "graph": {"id": "workflow2"},
        "links": links,
        "nodes": nodes,
    }

    # Eplicit check that the task didn't finish successfully
    expected_results = {"Python Error Handler Test": None}

    return graph, expected_results


def test_workflow2(ppf_log_config, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow2()
    err_msg = "Intentional error in pythonErrorHandlerTest!"

    with pytest.raises(RuntimeError, match=err_msg):
        execute_graph(graph, varinfo=varinfo)

    # The workflow failed so there are no results
    result = execute_graph(graph, varinfo=varinfo, raise_on_error=False)
    assert result == dict()
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
