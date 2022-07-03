from ewoksutils.import_utils import qualname
from ewokscore import Task
from ewoksppf import execute_graph


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
        {"id": "task1", "task_type": "class", "task_identifier": myclass},
        {"id": "task2", "task_type": "class", "task_identifier": myclass},
        {"id": "task3", "task_type": "class", "task_identifier": myclass},
        {"id": "task4", "task_type": "class", "task_identifier": myclass},
        {"id": "task5", "task_type": "class", "task_identifier": myclass},
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
                {"source_output": "b", "value": None},
            ],
        },
        {"source": "task4", "target": "task2", "map_all_data": True},
        {"source": "task5", "target": "task2", "map_all_data": True},
    ]

    graph = {"graph": {"id": "test_graph"}, "links": links, "nodes": nodes}

    expected_results = {"a": 9, "b": 9}

    return graph, expected_results


def test_ppf_end(ppf_log_config):
    graph, expected = workflow()
    result = execute_graph(graph)
    for k, v in expected.items():
        assert result[k] == v, k
