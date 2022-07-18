import pytest
from ewoksutils.import_utils import qualname
from ewokscore.tests.utils.results import assert_execute_graph_default_result
from ewoksppf import execute_graph


def passthrough(**kw):
    assert len(kw) == 1
    return next(iter(kw.values()))


def greater_than(a):
    return a > LIMIT


def raise_not_greater_than(a):
    assert a > LIMIT
    return True


def submodel21_conditions():
    """This submodel receives a value and returns True or False"""
    nodes = [
        {
            "id": "gt",
            "task_type": "method",
            "task_identifier": qualname(greater_than),
        },
    ]

    graph = {
        "id": "submodel21",
        "input_nodes": [
            {"id": "in", "node": "gt"},
        ],
        "output_nodes": [
            {
                "id": "true",
                "node": "gt",
                "link_attributes": {
                    "conditions": [{"source_output": "return_value", "value": True}]
                },
            },
            {
                "id": "false",
                "node": "gt",
                "link_attributes": {
                    "conditions": [{"source_output": "return_value", "value": False}]
                },
            },
        ],
    }

    graph = {
        "graph": graph,
        "nodes": nodes,
    }

    return graph


def submodel21_on_error():
    """This submodel receives a value and returns True or False"""
    nodes = [
        {
            "id": "gt",
            "task_type": "method",
            "task_identifier": qualname(raise_not_greater_than),
        },
    ]

    graph = {
        "id": "submodel21",
        "input_nodes": [
            {"id": "in", "node": "gt"},
        ],
        "output_nodes": [
            {
                "id": "true",
                "node": "gt",
            },
            {
                "id": "false",
                "node": "gt",
                "link_attributes": {"on_error": True},
            },
        ],
    }

    graph = {
        "graph": graph,
        "nodes": nodes,
    }

    return graph


def workflow21(on_error):
    if on_error:
        submodel21 = submodel21_on_error
    else:
        submodel21 = submodel21_conditions

    nodes = [
        {"id": "in", "task_type": "method", "task_identifier": qualname(passthrough)},
        {"id": "submodel", "task_type": "graph", "task_identifier": submodel21()},
        {
            "id": "out1",
            "task_type": "method",
            "task_identifier": qualname(passthrough),
            "default_inputs": [{"name": "a", "value": 1}],
        },
        {
            "id": "out2",
            "task_type": "method",
            "task_identifier": qualname(passthrough),
            "default_inputs": [{"name": "a", "value": 2}],
        },
        {"id": "out", "task_type": "method", "task_identifier": qualname(passthrough)},
    ]

    links = [
        {
            "source": "in",
            "target": "submodel",
            "sub_target": "gt",
            "data_mapping": [{"source_output": "return_value", "target_input": "a"}],
        },
        {"source": "submodel", "sub_source": "true", "target": "out1"},
        {"source": "submodel", "sub_source": "false", "target": "out2"},
        {
            "source": "out1",
            "target": "out",
            "data_mapping": [{"source_output": "return_value", "target_input": "a"}],
        },
        {
            "source": "out2",
            "target": "out",
            "data_mapping": [{"source_output": "return_value", "target_input": "b"}],
        },
    ]

    graph = {
        "graph": {"id": "workflow21"},
        "links": links,
        "nodes": nodes,
    }

    return graph


LIMIT = 10  # a > LIMIT
ARG_SUCCESS = {"inputs": {"a": 20}, "return_value": 1}
ARG_FAILURE = {"inputs": {"a": 0}, "return_value": 2}


@pytest.mark.parametrize(
    "args",
    [ARG_SUCCESS, ARG_FAILURE],
)
@pytest.mark.parametrize("on_error", [True, False])
@pytest.mark.parametrize("persist", [True, False])
def test_workflow21(args, on_error, persist, ppf_log_config, tmpdir):
    """Test conditions in output nodes"""
    if persist:
        varinfo = {"root_uri": str(tmpdir)}
    else:
        varinfo = None
    graph = workflow21(on_error=on_error)
    inputs = [{"name": k, "value": v} for k, v in args["inputs"].items()]
    result = execute_graph(graph, inputs=inputs, varinfo=varinfo)
    assert result
    assert result["return_value"] == args["return_value"]

    if args == ARG_SUCCESS:
        expected = {"a": 1, "return_value": args["return_value"]}
    else:
        expected = {"b": 2, "return_value": args["return_value"]}
    assert_execute_graph_default_result(graph, result, expected, varinfo=varinfo)
