from ewoksppf import job
from ewokscore.tests.utils import assert_taskgraph_result


def submodel16a():
    nodes = [
        {
            "id": "addtask1",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "in", "ppfport": "input"},
        {"id": "out", "ppfport": "output"},
    ]

    links = [
        {"source": "in", "target": "addtask1", "all_arguments": True},
        {"source": "addtask1", "target": "addtask2", "all_arguments": True},
        {"source": "addtask2", "target": "out", "all_arguments": True},
    ]

    graph = {
        "directed": True,
        "graph": {"name": "submodel16a"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def submodel16b():
    nodes = [
        {
            "id": "addtask1",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {
            "id": "addtask2",
            "ppfmethod": "ewoksppf.tests.test_ppf_actors.pythonActorAdd.run",
        },
        {"id": "submodel16a", "graph": submodel16a()},
        {"id": "in", "ppfport": "input"},
        {"id": "out", "ppfport": "output"},
    ]

    links = [
        {"source": "in", "target": "addtask1", "all_arguments": True},
        {
            "source": "addtask1",
            "target": "submodel16a",
            "links": [
                {
                    "source": "addtask1",
                    "target": "in",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel16a",
            "target": "addtask2",
            "links": [
                {
                    "source": "out",
                    "target": "addtask2",
                    "all_arguments": True,
                }
            ],
        },
        {"source": "addtask2", "target": "out", "all_arguments": True},
    ]

    graph = {
        "directed": True,
        "graph": {"name": "submodel16b"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    return graph


def workflow16():
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
        {"id": "submodel16b", "graph": submodel16b()},
    ]

    links = [
        {
            "source": "addtask1",
            "target": "submodel16b",
            "links": [
                {
                    "source": "addtask1",
                    "target": "in",
                    "all_arguments": True,
                }
            ],
        },
        {
            "source": "submodel16b",
            "target": "addtask2",
            "links": [
                {
                    "source": ("submodel16a", "out"),
                    "target": "addtask2",
                    "all_arguments": True,
                }
            ],
        },
    ]

    graph = {
        "directed": True,
        "graph": {"name": "workflow16"},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "addtask1": {"ppfdict": {"value": 2}},
        ("submodel16b", "in"): {"ppfdict": {"value": 2}},
        ("submodel16b", "addtask1"): {"ppfdict": {"value": 3}},
        ("submodel16b", ("submodel16a", "in")): {"ppfdict": {"value": 3}},
        ("submodel16b", ("submodel16a", "addtask1")): {"ppfdict": {"value": 4}},
        ("submodel16b", ("submodel16a", "addtask2")): {"ppfdict": {"value": 5}},
        ("submodel16b", ("submodel16a", "out")): {
            "ppfdict": {"value": 5}
        },  # 2 destinations
        ("submodel16b", "addtask2"): {"ppfdict": {"value": 6}},
        ("submodel16b", "out"): {"ppfdict": {"value": 6}},
        "addtask2": {"ppfdict": {"value": 6}},
    }

    return graph, expected_results


def test_workflow16(ppf_logging, tmpdir):
    """Test connecting nodes from sub-submodels to the top model"""
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = workflow16()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)
