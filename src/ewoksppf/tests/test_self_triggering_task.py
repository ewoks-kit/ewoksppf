import pytest
import os.path
from ewokscore import Task
from ewoksppf import execute_graph


qualname = __name__


def test_explicit_start_node_on_self_triggering_node(tmpdir):
    """
    Workflow:
     - LOOP depends on itself (self-triggering task).
     - SAVE depends on LOOP and CONFIG
     - CONFIG does not depend on anything

     /|
    / |
    LOOP -- SAVE
            /
           /
          /
    CONFIG

    This test tests that, while graph analysis considers that the only
    start node is CONFIG, it is possible to set `start_node` for LOOP
    and make it a start node so that SAVE can get inputs from LOOP and
    CONFIG.
    """

    class ConfigTask(Task, input_names=["filename"], output_names=["config"]):
        def run(self):
            self.outputs.config = {"filename": self.inputs.filename}

    class LoopTask(
        Task,
        input_names=["i", "n"],
        output_names=["i", "keep_looping"],
    ):
        def run(self):
            self.outputs.i = self.inputs.i + 1
            self.outputs.keep_looping = self.outputs.i < self.inputs.n

    class SaveTask(
        Task,
        input_names=["config"],
        optional_input_names=["i"],
        output_names=["result"],
    ):
        def run(self):
            if self.missing_inputs.i:
                raise RuntimeError("LOOP not executed!")
            config = self.inputs.config
            with open(config["filename"], "a") as out_file:
                out_file.write(f"LOOP executed: {self.inputs.i}")

    workflow = {
        "graph": {"id": "testworkflow"},
        "nodes": [
            {
                "id": "CONFIG",
                "task_type": "class",
                "task_identifier": f"{qualname}.ConfigTask",
            },
            {
                "id": "LOOP",
                "task_type": "class",
                "task_identifier": f"{qualname}.LoopTask",
            },
            {
                "id": "SAVE",
                "task_type": "class",
                "task_identifier": f"{qualname}.SaveTask",
            },
        ],
        "links": [
            {
                "source": "LOOP",
                "target": "LOOP",
                "data_mapping": [{"source_output": "i", "target_input": "i"}],
                "conditions": [{"source_output": "keep_looping", "value": True}],
            },
            {
                "source": "LOOP",
                "target": "SAVE",
                "data_mapping": [{"source_output": "i", "target_input": "i"}],
            },
            {
                "source": "CONFIG",
                "target": "SAVE",
                "data_mapping": [{"source_output": "config", "target_input": "config"}],
            },
        ],
    }

    filename = str(tmpdir / "test.txt")
    max_iterations = 10
    inputs = [
        {
            "task_identifier": f"{qualname}.ConfigTask",
            "name": "filename",
            "value": filename,
        },
        {
            "task_identifier": f"{qualname}.LoopTask",
            "name": "i",
            "value": 0,
        },
        {
            "task_identifier": f"{qualname}.LoopTask",
            "name": "n",
            "value": max_iterations,
        },
    ]

    # Execute without setting `force_start_node` in the LOOP node: the SAVE task fails.
    with pytest.raises(RuntimeError) as e:
        execute_graph(
            workflow,
            scaling_workers=False,
            pool_type="thread",
            inputs=inputs,
        )
        assert str(e) == "RuntimeError: Task 'SAVE' failed"
    assert not os.path.exists(filename)

    # Execute with `force_start_node` in the LOOP node; the SAVE task runs and the file exists.
    loop_node = workflow["nodes"][1]
    assert loop_node["id"] == "LOOP"
    loop_node["force_start_node"] = True

    execute_graph(
        workflow,
        scaling_workers=False,
        pool_type="thread",
        inputs=inputs,
    )

    with open(filename) as _file:
        txt = _file.read()
    for i in range(max_iterations):
        assert str(i) in txt
