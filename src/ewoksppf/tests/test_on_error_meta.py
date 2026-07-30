from time import sleep
from typing import List

import pytest
from ewokscore.task import Task
from ewoksutils.exceptions import TaskExecutionError
from pypushflow.WorkflowResults import WORKFLOW_EXCEPTION_INSTANCE_KEY
from pypushflow.WorkflowResults import WORKFLOW_EXCEPTION_KEY

from ..bindings import execute_graph


@pytest.fixture
def global_error_node() -> dict:
    return {
        "graph": {"id": "test"},
        "nodes": [
            {
                "id": "failing_node",
                "task_type": "class",
                "task_identifier": f"{__name__}.MyTask",
            },
            {
                "id": "meta_node",
                "task_type": "class",
                "task_identifier": f"{__name__}.ErrorMetadataTask",
                "default_error_attributes": {"cache_if_optional": True},
            },
            {
                "id": "error_handler",
                "task_type": "class",
                "task_identifier": f"{__name__}.ErrorHandler",
                "default_error_node": True,
            },
        ],
        "links": [
            {
                "source": "meta_node",
                "target": "error_handler",
                "map_all_data": True,
                "required": True,
            },
        ],
    }


@pytest.fixture
def explicit_error_node() -> dict:
    return {
        "graph": {"id": "test"},
        "nodes": [
            {
                "id": "failing_node",
                "task_type": "class",
                "task_identifier": f"{__name__}.MyTask",
            },
            {
                "id": "meta_node",
                "task_type": "class",
                "task_identifier": f"{__name__}.ErrorMetadataTask",
            },
            {
                "id": "error_handler",
                "task_type": "class",
                "task_identifier": f"{__name__}.ErrorHandler",
                "default_error_node": False,
            },
        ],
        "links": [
            {
                "source": "meta_node",
                "target": "error_handler",
                "map_all_data": True,
                "required": True,
            },
            {
                "source": "failing_node",
                "target": "error_handler",
                "on_error": True,
                "map_all_data": True,
                "cache_if_optional": True,
            },
        ],
    }


def test_default_error_node_metadata_error_first(global_error_node):
    inputs = [
        {"id": "failing_node", "name": "sleep", "value": 0.0},
        {"id": "meta_node", "name": "sleep", "value": 0.1},
    ]
    _assert_failure(global_error_node, inputs)


def test_default_error_node_metadata_meta_first(global_error_node):
    inputs = [
        {"id": "failing_node", "name": "sleep", "value": 0.1},
        {"id": "meta_node", "name": "sleep", "value": 0.0},
    ]
    _assert_failure(global_error_node, inputs)


def test_on_error_link_metadata_error_first(explicit_error_node):
    inputs = [
        {"id": "failing_node", "name": "sleep", "value": 0.0},
        {"id": "meta_node", "name": "sleep", "value": 0.1},
    ]
    _assert_failure(explicit_error_node, inputs)


def test_on_error_link_metadata_meta_first(explicit_error_node):
    inputs = [
        {"id": "failing_node", "name": "sleep", "value": 0.1},
        {"id": "meta_node", "name": "sleep", "value": 0.0},
    ]
    _assert_failure(explicit_error_node, inputs)


class CustomError(Exception):
    pass


class MyTask(Task, input_names=["sleep"]):
    def run(self):
        sleep(self.inputs.sleep)
        raise CustomError("original error message")


class ErrorMetadataTask(Task, input_names=["sleep"], output_names=["metadata"]):
    def run(self):
        sleep(self.inputs.sleep)
        self.outputs.metadata = True


class ErrorHandler(
    Task,
    input_names=["metadata"],
    optional_input_names=[WORKFLOW_EXCEPTION_KEY, WORKFLOW_EXCEPTION_INSTANCE_KEY],
):
    def run(self):
        exception = getattr(self.inputs, WORKFLOW_EXCEPTION_INSTANCE_KEY)
        if exception:
            assert self.inputs.metadata
            raise exception


def _assert_failure(workflow: dict, inputs: List[dict]) -> None:
    with pytest.raises(TaskExecutionError, match="original error message") as exc_info:
        execute_graph(workflow, inputs=inputs, pool_type="thread")

    expected = f"Execution failed for ewoks task 'failing_node' (id: 'failing_node', task: '{__name__}.MyTask'): original error message"
    assert isinstance(exc_info.value.__cause__, TaskExecutionError)
    assert str(exc_info.value.__cause__) == expected

    expected = "original error message"
    assert isinstance(exc_info.value.__cause__.__cause__, CustomError)
    assert str(exc_info.value.__cause__.__cause__) == expected
