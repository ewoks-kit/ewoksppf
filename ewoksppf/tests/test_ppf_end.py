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
        {"source": "task1", "target": "task2", "all_arguments": True},
        {"source": "task2", "target": "task3", "all_arguments": True},
        {
            "source": "task3",
            "target": "task4",
            "all_arguments": True,
            "conditions": {"a": 3, "b": 3},
        },
        {
            "source": "task3",
            "target": "task5",
            "all_arguments": True,
            "conditions": {"a": 6, "b": "other"},
        },
        {"source": "task4", "target": "task2", "all_arguments": True},
        {"source": "task5", "target": "task2", "all_arguments": True},
    ]

    graph = {"links": links, "nodes": nodes}

    expected_results = {"a": 10}

    return graph, expected_results


@pytest.mark.skip("TODO")
def test_ppf_end(ppf_logging):
    graph, expected = workflow()
    result = execute_graph(graph)
    for k, v in expected.items():
        assert result[k] == v, k
