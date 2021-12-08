from ewoksppf import execute_graph


def workflow19():

    sum3 = "ewoksppf.tests.test_ppf_actors.pythonActorAddABC2D.run"
    incrementation = (
        "ewoksppf.tests.test_ppf_actors.pythonActorDiamondTest.run_incrementation"
    )
    no_processing = (
        "ewoksppf.tests.test_ppf_actors.pythonActorDiamondTest.no_processing"
    )
    move_d_to_a = "ewoksppf.tests.test_ppf_actors.pythonActorDiamondTest.move_d_to_a"
    nodes = [
        {
            "id": "task1",
            "task_type": "ppfmethod",
            "task_identifier": sum3,
            "default_inputs": [
                {"name": "a", "value": 1},
                {"name": "b", "value": 2},
                {"name": "c", "value": 4},
            ],
            "inputs_complete": True,
        },
        {"id": "task2", "task_type": "ppfmethod", "task_identifier": move_d_to_a},
        {
            "id": "task3",
            "task_type": "ppfmethod",
            "task_identifier": incrementation,
            "default_inputs": [{"name": "increment_value", "value": 1}],
        },
        {"id": "task4", "task_type": "ppfmethod", "task_identifier": no_processing},
        {"id": "task5", "task_type": "ppfmethod", "task_identifier": no_processing},
    ]
    links = [
        {"source": "task1", "target": "task2", "map_all_data": True},
        {
            "source": "task2",
            "target": "task3",
            "map_all_data": True,
            "conditions": [{"source_output": "d", "value": 7}],
        },
        {
            "source": "task2",
            "target": "task4",
            "map_all_data": True,
            "conditions": [{"source_output": "d", "value": 13}],
        },
        {
            "source": "task2",
            "target": "task5",
            "map_all_data": True,
            "conditions": [{"source_output": "d", "value": "__other__"}],
        },
        {"source": "task3", "target": "task1", "map_all_data": True},
        {"source": "task4", "target": "task1", "map_all_data": True},
    ]
    graph = {
        "graph": {"id": "workflow19"},
        "links": links,
        "nodes": nodes,
    }
    expected_results = {
        "_ppfdict": {"a": 18, "b": 1, "c": 4, "d": 18, "increment_value": 1}
    }

    return graph, expected_results


def test_workflow19(ppf_log_config, tmpdir):
    """Test 2 unconditional upstream tasks, one coming from a feedback loop"""
    graph, expected = workflow19()
    result = execute_graph(graph)
    for k in expected:
        assert result[k] == expected[k]
