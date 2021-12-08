import pytest
from ewoksppf import execute_graph


def workflow17(doloop=True):
    if doloop:
        condition = 3
        result = 7
    else:
        condition = 1000
        result = 3

    ppfmethod = "ewoksppf.tests.test_ppf_actors.pythonActorAddWithoutSleep.run"
    nodes = [
        {
            "id": "task1",
            "task_type": "ppfmethod",
            "task_identifier": ppfmethod,
            "default_inputs": [{"name": "value", "value": 0}],
        },
        {"id": "task2", "task_type": "ppfmethod", "task_identifier": ppfmethod},
        {"id": "task3", "task_type": "ppfmethod", "task_identifier": ppfmethod},
        {"id": "task4", "task_type": "ppfmethod", "task_identifier": ppfmethod},
        {"id": "task5", "task_type": "ppfmethod", "task_identifier": ppfmethod},
    ]
    links = [
        {"source": "task1", "target": "task2", "map_all_data": True},
        {"source": "task2", "target": "task3", "map_all_data": True},
        {
            "source": "task3",
            "target": "task4",
            "map_all_data": True,
            "conditions": [{"source_output": "value", "value": condition}],
        },
        {"source": "task4", "target": "task5", "map_all_data": True},
        {"source": "task5", "target": "task2", "map_all_data": True},
    ]
    graph = {
        "graph": {"id": "workflow17"},
        "links": links,
        "nodes": nodes,
    }

    expected_result = {"_ppfdict": {"value": result}}

    return graph, expected_result


@pytest.mark.parametrize("doloop", [True, False])
def test_workflow17(doloop, ppf_log_config):
    """Test 2 unconditional upstream tasks, one coming from a feedback loop"""
    graph, expected = workflow17(doloop=doloop)
    result = execute_graph(graph)
    for k, v in expected.items():
        assert result[k] == v, k
