import os
import threading

import pytest
from ewokscore.task import Task
from ewoksutils.import_utils import qualname

from ewoksppf import execute_graph

_NUM_IMAGES = 100
_INTEGRATED = list()
_LOCK = threading.Lock()


class InitIntegrator(Task, input_names=["params_file"], output_names=["integrator"]):
    def run(self):
        self.outputs.integrator = f"Integrator({self.inputs.params_file})"


class FindImages(
    Task,
    input_names=["image_directory", "integrator"],
    optional_input_names=["image_index"],
    output_names=["image_path", "next_image_index", "finished", "integrator"],
):
    def run(self):
        image_index = self.get_input_value("image_index", 0)
        self.outputs.image_path = os.path.join(
            self.inputs.image_directory, f"data{image_index}.tiff"
        )
        self.outputs.next_image_index = image_index + 1
        self.outputs.finished = self.outputs.next_image_index == _NUM_IMAGES
        self.outputs.integrator = self.inputs.integrator


class IntegrateImage(Task, input_names=["integrator", "image_path"]):
    def run(self):
        with _LOCK:
            _INTEGRATED.append((self.inputs.integrator, self.inputs.image_path))


def workflow29():
    nodes = [
        {
            "id": "init_integrator",
            "task_type": "class",
            "task_identifier": qualname(InitIntegrator),
        },
        {
            "id": "find_images",
            "task_type": "class",
            "task_identifier": qualname(FindImages),
        },
        {
            "id": "integrate_image",
            "task_type": "class",
            "task_identifier": qualname(IntegrateImage),
        },
    ]
    links = [
        {
            "source": "init_integrator",
            "target": "find_images",
            "data_mapping": [
                {"source_output": "integrator", "target_input": "integrator"}
            ],
        },
        {
            "source": "find_images",
            "target": "find_images",
            "data_mapping": [
                {"source_output": "next_image_index", "target_input": "image_index"},
            ],
            "conditions": [{"source_output": "finished", "value": False}],
        },
        {
            "source": "find_images",
            "target": "integrate_image",
            "data_mapping": [
                {"source_output": "image_path", "target_input": "image_path"},
                {"source_output": "integrator", "target_input": "integrator"},
            ],
        },
    ]
    return {"graph": {"id": "workflow29"}, "links": links, "nodes": nodes}


@pytest.mark.parametrize("scaling_workers", [False, True])
def test_workflow29(ppf_log_config, scaling_workers):
    """A self-looping task should be able to iterate many times without
    a RecursionError or a closed pool (issue #22)."""
    inputs = [
        {"id": "init_integrator", "name": "params_file", "value": "calib.poni"},
        {"id": "find_images", "name": "image_directory", "value": "data"},
    ]
    kwargs = {"scaling_workers": True, "max_workers": 2} if scaling_workers else {}
    _INTEGRATED.clear()
    execute_graph(workflow29(), inputs=inputs, pool_type="thread", timeout=60, **kwargs)
    expected = [
        ("Integrator(calib.poni)", os.path.join("data", f"data{i}.tiff"))
        for i in range(_NUM_IMAGES)
    ]
    assert sorted(_INTEGRATED) == sorted(expected)
