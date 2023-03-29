from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


def workflow():
    nodes = [
        {
            "id": "Before loop",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddA.run",
            "default_inputs": [
                {"name": "a", "value": 1},
                {"name": "b", "value": 1},
                {"name": "a_is_5", "value": False},
                {"name": "b_is_4", "value": False},
            ],
        },
        {
            "id": "AddA in loop",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddA.run",
        },
        {
            "id": "AddB in loop",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddB.run",
        },
        {
            "id": "AddA outside loop",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddA.run",
        },
        {
            "id": "AddB outside loop",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAddB.run",
        },
    ]
    links = [
        {
            "source": "Before loop",
            "target": "AddA in loop",
            "map_all_data": True,
        },
        {
            "source": "AddA in loop",
            "target": "AddB in loop",
            "map_all_data": True,
            "conditions": [
                {"source_output": "a_is_5", "value": False},
                {"source_output": "b_is_4", "value": False},
            ],
        },
        {
            "source": "AddB in loop",
            "target": "AddA in loop",
            "map_all_data": True,
        },
        {
            "source": "AddA in loop",
            "target": "AddA outside loop",
            "map_all_data": True,
            "conditions": [
                {"source_output": "a_is_5", "value": True},
                {"source_output": "b_is_4", "value": False},
            ],
        },
        {
            "source": "AddA in loop",
            "target": "AddB outside loop",
            "map_all_data": True,
            "conditions": [
                {"source_output": "a_is_5", "value": True},
                {"source_output": "b_is_4", "value": True},
            ],
        },
    ]

    graph = {"graph": {"id": "workflow22"}, "links": links, "nodes": nodes}

    expected_results = {"a": 6, "a_is_5": False, "b": 3, "b_is_4": False}

    return graph, expected_results


def test_ppf_workflow22(ppf_log_config, tmpdir):
    """This is a test of a loop with several conditions for exiting the loop."""
    # The execution should be like this:
    #   Initial conditions: {"a": 1, "a_is_5": False, "b": 1, "b_is_4": False}
    #   After 'Before loop': {"a": 2, "a_is_5": False, "b": 1, "b_is_4": False}
    #   After 'AddA in loop' : {"a": 3, "a_is_5": False, "b": 1, "b_is_4": False}
    #   After 'AddB in loop' : {"a": 3, "a_is_5": False, "b": 2, "b_is_4": False}
    #   After 'AddA in loop' : {"a": 4, "a_is_5": False, "b": 2, "b_is_4": False}
    #   After 'AddB in loop' : {"a": 4, "a_is_5": False, "b": 3, "b_is_4": False}
    #   After 'AddA in loop' : {"a": 5, "a_is_5": True, "b": 1, "b_is_4": False}
    #   After 'AddA outside loop': {"a": 6, "a_is_5": False, "b": 1, "b_is_4": False}

    graph, expected = workflow()
    varinfo = {"root_uri": str(tmpdir)}
    result = execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
