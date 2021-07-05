import pytest
from ewoksppf import job


def workflow17(doloop=True):
    if doloop:
        condition = 3
        result = 7
    else:
        condition = 1000
        result = 3

    ppfmethod = "ewoksppf.tests.test_ppf_actors.pythonActorAddWithoutSleep.run"
    nodes = [
        {"id": "task1", "ppfmethod": ppfmethod, "inputs": {"value": 0}},
        {"id": "task2", "ppfmethod": ppfmethod},
        {"id": "task3", "ppfmethod": ppfmethod},
        {"id": "task4", "ppfmethod": ppfmethod},
        {"id": "task5", "ppfmethod": ppfmethod},
    ]
    links = [
        {"source": "task1", "target": "task2", "all_arguments": True},
        {"source": "task2", "target": "task3", "all_arguments": True},
        {
            "source": "task3",
            "target": "task4",
            "all_arguments": True,
            "conditions": {"value": condition},
        },
        {"source": "task4", "target": "task5", "all_arguments": True},
        {"source": "task5", "target": "task2", "all_arguments": True},
    ]
    graph = {
        "graph": {"name": "workflow17"},
        "links": links,
        "nodes": nodes,
    }

    expected_result = {"ppfdict": {"value": result}}

    return graph, expected_result


@pytest.mark.parametrize("doloop", [True, False])
def test_workflow17(doloop, ppf_logging):
    """Test 2 unconditional upstream tasks, one coming from a feedback loop"""
    graph, expected = workflow17(doloop=doloop)
    result = job(graph)
    for k, v in expected.items():
        assert result[k] == v, k
