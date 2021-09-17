from ewoksppf import execute_graph
from ewokscore.tests.utils import assert_taskgraph_result


def workflow9():
    nodes = [
        {
            "id": "addtask1",
            "default_inputs": [{"name": "value", "value": 1}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask3",
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
    ]

    links = [
        {
            "source": "addtask1",
            "target": "addtask2",
            "conditions": [{"source_output": "value", "value": 2}],
            "map_all_data": True,
        },
        {
            "source": "addtask1",
            "target": "addtask3",
            "conditions": [{"source_output": "value", "value": 3}],
            "map_all_data": True,
        },
    ]

    graph = {
        "graph": {"name": "workflow9"},
        "links": links,
        "nodes": nodes,
    }

    # addtask3 will not be executed explicitly but it represents
    # the same task instance as addtask2 (same task hash). So it
    # will appear as "done" and have a result.
    expected_results = {
        "addtask1": {"ppfdict": {"value": 2}},
        "addtask2": {"ppfdict": {"value": 3}},
        "addtask3": {"ppfdict": {"value": 3}},
    }

    return graph, expected_results


def test_workflow9(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow9()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo=varinfo)
