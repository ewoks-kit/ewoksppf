import itertools
import pytest
from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_workflow_merged_result


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
        "graph": {"name": "workflow10"},
        "links": links,
        "nodes": nodes,
    }

    limit = inputs["limit"]
    expected_result = {
        "ppfdict": {"doContinue": "false", "limit": limit, "value": limit}
    }

    return graph, expected_result


@pytest.mark.parametrize(
    "limit,persistent",
    itertools.product([10], [True, False]),
)
def test_workflow10(limit, persistent, ppf_logging, tmpdir):
    if persistent:
        varinfo = {"root_uri": str(tmpdir)}
    else:
        varinfo = {}
    inputs = {"value": 1, "limit": limit}
    graph, expected = workflow10(inputs)
    result = execute_graph(graph, varinfo=varinfo)
    if persistent:
        assert_workflow_merged_result(result, expected, varinfo)
    else:
        assert len(tmpdir.listdir()) == 0
        for k in expected:
            assert result[k] == expected[k]
