import pytest
from ewoksppf import execute_graph
from ewokscore import Task
from ewokscore.utils import qualname


class MyTask(Task, optional_input_names=["a", "b"], output_names=["a", "b"]):
    def run(self):
        if self.inputs.a:
            self.outputs.a = self.inputs.a + 1
        else:
            self.outputs.a = 1
        if self.inputs.b:
            self.outputs.b = self.inputs.b + 1
        else:
            self.outputs.b = 1


def workflow():
    myclass = qualname(MyTask)
    nodes = [
        {"id": "task1", "class": myclass},
        {"id": "task2", "class": myclass},
        {"id": "task3", "class": myclass},
        {"id": "task4", "class": myclass},
        {"id": "task5", "class": myclass},
    ]
    links = [
        {"source": "task1", "target": "task2", "map_all_data": True},
        {"source": "task2", "target": "task3", "map_all_data": True},
        {
            "source": "task3",
            "target": "task4",
            "map_all_data": True,
            "conditions": [
                {"source_output": "a", "value": 3},
                {"source_output": "b", "value": 3},
            ],
        },
        {
            "source": "task3",
            "target": "task5",
            "map_all_data": True,
            "conditions": [
                {"source_output": "a", "value": 6},
                {"source_output": "b", "value": "other"},
            ],
        },
        {"source": "task4", "target": "task2", "map_all_data": True},
        {"source": "task5", "target": "task2", "map_all_data": True},
    ]

    graph = {"links": links, "nodes": nodes}

    expected_results = {"a": 10}

    return graph, expected_results


@pytest.mark.skip("TODO")
def test_ppf_end(ppf_log_config):
    graph, expected = workflow()
    result = execute_graph(graph)
    for k, v in expected.items():
        assert result[k] == v, k
