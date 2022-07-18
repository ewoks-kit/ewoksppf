import pytest
from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_values


def workflow10(inputs):
    default_inputs = [{"name": name, "value": value} for name, value in inputs.items()]
    nodes = [
        {
            "id": "addWithoutSleep",
            "default_inputs": default_inputs,
            "inputs_complete": True,
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddWithoutSleep.run",
        },
        {
            "id": "check",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorCheck.run",
        },
    ]

    links = [
        {
            "source": "addWithoutSleep",
            "target": "check",
            "map_all_data": True,
        },
        {
            "source": "check",
            "target": "addWithoutSleep",
            "conditions": [{"source_output": "doContinue", "value": "true"}],
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"id": "workflow10"},
        "links": links,
        "nodes": nodes,
    }

    limit = inputs["limit"]
    expected_result = {
        "_ppfdict": {"doContinue": "false", "limit": limit, "value": limit}
    }

    return graph, expected_result


@pytest.mark.parametrize("limit", [10])
@pytest.mark.parametrize("scheme", [None, "json"])
def test_workflow10(limit, scheme, ppf_log_config, tmpdir):
    if scheme:
        varinfo = {"root_uri": str(tmpdir), "scheme": scheme}
    else:
        varinfo = {}
    inputs = {"value": 1, "limit": limit}
    graph, expected = workflow10(inputs)
    result = execute_graph(graph, varinfo=varinfo)
    if scheme:
        assert_execute_graph_values(result, expected, varinfo)
    else:
        assert len(tmpdir.listdir()) == 0
        for k in expected:
            assert result[k] == expected[k]
