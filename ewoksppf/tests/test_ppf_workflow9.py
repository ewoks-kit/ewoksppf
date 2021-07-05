from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def workflow9():
    nodes = [
        {
            "id": "addtask1",
            "inputs": {"value": 1},
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask3",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
    ]

    links = [
        {
            "source": "addtask1",
            "target": "addtask2",
            "conditions": {"value": 2},
            "all_arguments": True,
        },
        {
            "source": "addtask1",
            "target": "addtask3",
            "conditions": {"value": 3},
            "all_arguments": True,
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow9"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    # addtask3 will not be executed explicitely but it represents
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
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
