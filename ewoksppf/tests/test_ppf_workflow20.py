import pytest
from ewoksppf import execute_graph


def workflow20():
    ppfmethod = "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run"
    nodes = [
        {"id": "task1", "task_type": "ppfmethod", "task_identifier": ppfmethod},
        {"id": "task2", "task_type": "ppfmethod", "task_identifier": ppfmethod},
    ]

    links = [{"source": "task1", "target": "task2", "map_all_data": True}]

    graph = {
        "links": links,
        "nodes": nodes,
    }

    return graph


@pytest.mark.parametrize("persist", [True, False])
def test_workflow20(persist, ppf_log_config, tmpdir):
    if persist:
        varinfo = {"root_uri": str(tmpdir)}
    else:
        varinfo = None
    graph = workflow20()
    result = execute_graph(
        graph, inputs=[{"name": "value", "value": 5}], varinfo=varinfo
    )
    assert result["_ppfdict"]["value"] == 7
