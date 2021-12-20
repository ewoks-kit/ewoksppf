from ewoksppf import execute_graph
from ewokscore.tests.utils.results import assert_execute_graph_all_tasks


def submodel1():
    nodes = [
        {
            "id": "mytask",
            "default_inputs": [{"name": "name", "value": "myname"}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
    ]

    links = []

    graph = {
        "graph": {"name": "submodel1"},
        "links": links,
        "nodes": nodes,
    }

    return graph


def workflow3():
    nodes = [
        {
            "id": "first",
            "default_inputs": [{"name": "name", "value": "first"}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
        {
            "id": "last",
            "default_inputs": [{"name": "name", "value": "last"}],
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorTest.run",
        },
        {"id": "middle", "task_type": "graph", "task_identifier": submodel1()},
    ]

    links = [
        {
            "source": "first",
            "target": "middle",
            "sub_target": "mytask",
            "sub_target_attributes": {
                "default_inputs": [{"name": "name", "value": "middle"}],
            },
        },
        {
            "source": "middle",
            "sub_source": "mytask",
            "target": "last",
        },
    ]

    graph = {
        "graph": {"id": "workflow3"},
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "first": {"_ppfdict": {"name": "first", "reply": "Hello first!"}},
        ("middle", "mytask"): {
            "_ppfdict": {"name": "middle", "reply": "Hello middle!"}
        },
        "last": {"_ppfdict": {"name": "last", "reply": "Hello last!"}},
    }

    return graph, expected_results


def test_workflow3(ppf_log_config, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow3()
    execute_graph(graph, varinfo=varinfo)
    assert_execute_graph_all_tasks(graph, expected, varinfo=varinfo)
