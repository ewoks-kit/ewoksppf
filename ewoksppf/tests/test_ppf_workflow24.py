from ewoksutils.import_utils import qualname
from ewoksppf import execute_graph


def myfunc(name=None, succeeded=tuple(), raise_on_names=tuple(), **_):
    if name in raise_on_names:
        raise RuntimeError(f"raise on name: {name}")
    succeeded += (name,)
    return {"succeeded": succeeded}


def task1(**kw):
    return myfunc(name="task1", **kw)


def task2(**kw):
    return myfunc(name="task2", **kw)


def task3(**kw):
    return myfunc(name="task3", **kw)


def subtask1(**kw):
    return myfunc(name="subtask1", **kw)


def subtask2(**kw):
    return myfunc(name="subtask2", **kw)


def subtask3(**kw):
    return myfunc(name="subtask3", **kw)


def subsubtask1(**kw):
    return myfunc(name="subsubtask1", **kw)


def subsubtask2(**kw):
    return myfunc(name="subsubtask2", **kw)


def subsubtask3(**kw):
    return myfunc(name="subsubtask3", **kw)


def subsub_handler(**kw):
    return myfunc(name="subsub_handler", **kw)


def subsubmodel():
    graph = {
        "id": "subsubmodel",
        "input_nodes": [{"id": "in", "node": "subsubtask1"}],
        "output_nodes": [{"id": "out", "node": "subsubtask3"}],
    }
    nodes = [
        {
            "id": "subsubtask1",
            "task_type": "ppfmethod",
            "task_identifier": qualname(subsubtask1),
        },
        {
            "id": "subsubtask2",
            "task_type": "ppfmethod",
            "task_identifier": qualname(subsubtask2),
        },
        {
            "id": "subsubtask3",
            "task_type": "ppfmethod",
            "task_identifier": qualname(subsubtask3),
        },
        {
            "id": "subsub_handler",
            "task_type": "ppfmethod",
            "task_identifier": qualname(subsub_handler),
            "default_error_node": True,
        },
    ]
    links = [
        {"source": "subsubtask1", "target": "subsubtask2", "map_all_data": True},
        {"source": "subsubtask2", "target": "subsubtask3", "map_all_data": True},
    ]
    return {"graph": graph, "nodes": nodes, "links": links}


def submodel():
    graph = {
        "id": "submodel",
        "input_nodes": [{"id": "in", "node": "subtask1"}],
        "output_nodes": [{"id": "out", "node": "subtask3"}],
    }
    nodes = [
        {
            "id": "subtask1",
            "task_type": "ppfmethod",
            "task_identifier": qualname(subtask1),
        },
        {
            "id": "subtask2",
            "task_type": "ppfmethod",
            "task_identifier": qualname(subtask2),
        },
        {
            "id": "subtask3",
            "task_type": "ppfmethod",
            "task_identifier": qualname(subtask3),
        },
        {
            "id": "sub_handler",
            "task_type": "graph",
            "task_identifier": subsubmodel(),
            "default_error_node": True,
        },
    ]
    links = [
        {"source": "subtask1", "target": "subtask2", "map_all_data": True},
        {"source": "subtask2", "target": "subtask3", "map_all_data": True},
    ]
    return {"graph": graph, "nodes": nodes, "links": links}


def workflow():
    nodes = [
        {
            "id": "task1",
            "task_type": "ppfmethod",
            "task_identifier": qualname(task1),
        },
        {
            "id": "task2",
            "task_type": "ppfmethod",
            "task_identifier": qualname(task2),
        },
        {
            "id": "task3",
            "task_type": "ppfmethod",
            "task_identifier": qualname(task3),
        },
        {
            "id": "top_handler",
            "task_type": "graph",
            "task_identifier": submodel(),
            "default_error_node": True,
        },
    ]
    links = [
        {"source": "task1", "target": "task2", "map_all_data": True},
        {"source": "task2", "target": "task3", "map_all_data": True},
    ]
    return {"graph": {"id": "workflow"}, "nodes": nodes, "links": links}


def test_ppf_workflow24(ppf_log_config):
    """test default error handlers"""

    inputs = [
        {"name": "succeeded", "value": tuple()},
        {"name": "raise_on_names", "value": tuple()},
    ]
    result = execute_graph(workflow(), inputs=inputs, raise_on_error=False)
    succeeded = "task1", "task2", "task3"
    assert result["_ppfdict"]["succeeded"] == succeeded
    assert "WorkflowException" not in result["_ppfdict"]

    inputs = [
        {"name": "succeeded", "value": tuple()},
        {"name": "raise_on_names", "value": ("task3",)},
    ]
    result = execute_graph(workflow(), inputs=inputs, raise_on_error=False)
    succeeded = "task1", "task2", "subtask1", "subtask2", "subtask3"
    assert result["_ppfdict"]["succeeded"] == succeeded
    errorMessage = result["_ppfdict"]["WorkflowException"]["errorMessage"]
    assert errorMessage == "Task 'task3' failed"

    inputs = [
        {"name": "succeeded", "value": tuple()},
        {"name": "raise_on_names", "value": ("task3", "subtask2")},
    ]
    result = execute_graph(workflow(), inputs=inputs, raise_on_error=False)
    succeeded = (
        "task1",
        "task2",
        "subtask1",
        "subsubtask1",
        "subsubtask2",
        "subsubtask3",
    )
    assert result["_ppfdict"]["succeeded"] == succeeded
    errorMessage = result["_ppfdict"]["WorkflowException"]["errorMessage"]
    assert errorMessage == "Task 'task3' failed"

    inputs = [
        {"name": "succeeded", "value": tuple()},
        {"name": "raise_on_names", "value": ("task3", "subtask3", "subsubtask1")},
    ]
    result = execute_graph(workflow(), inputs=inputs, raise_on_error=False)
    succeeded = "task1", "task2", "subtask1", "subtask2", "subsub_handler"
    assert result["_ppfdict"]["succeeded"] == succeeded
    errorMessage = result["_ppfdict"]["WorkflowException"]["errorMessage"]
    assert errorMessage == "Task 'task3' failed"
