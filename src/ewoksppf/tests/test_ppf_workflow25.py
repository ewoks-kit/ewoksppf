import time

from ewokscore.task import Task
from ewoksutils.import_utils import qualname

from ..bindings import execute_graph


class Required(Task, input_names=["compute_time"], output_names=["param1", "param2"]):
    def run(self):
        time.sleep(self.inputs.compute_time)
        self.outputs.param1 = -1
        self.outputs.param2 = -2


class Metric(Task, input_names=["compute_time", "metric"], output_names=["metric"]):
    def run(self):
        time.sleep(self.inputs.compute_time)
        self.outputs.metric = self.inputs.metric


class Timeout(Task, input_names=["timeout"], output_names=["timeout"]):
    def run(self):
        time.sleep(self.inputs.timeout)
        self.outputs.timeout = True


class Decider(
    Task,
    input_names=["param1", "param2", "metric_threshold"],
    optional_input_names=[
        "metric1",
        "metric2",
        "metric3",
        "metric4",
        "timeout",
        "disable",
    ],
    output_names=["good_enough", "reason", "set_disable"],
):
    def run(self):
        print("\nDecider inputs:", self.get_input_values())
        print("Metric threshold:", self.inputs.metric_threshold)
        if self.inputs.param1 != -1:
            raise ValueError(f"param1 is {self.inputs.param1} intead of -1")

        if self.inputs.param2 != -2:
            raise ValueError(f"param2 is {self.inputs.param2} intead of -2")

        if self.inputs.disable:
            print("IGNORE")
            self.outputs.good_enough = None
            self.outputs.reason = None
            self.outputs.set_disable = False
            return

        good_metrics = []
        nmetrics = 0
        for name in ["metric1", "metric2", "metric3", "metric4"]:
            value = self.get_input_value(name, None)
            if value is None:
                continue
            nmetrics += 1
            if value >= self.inputs.metric_threshold:
                good_metrics.append(name)
        print("Metrics that are good:", good_metrics)

        if any(good_metrics):
            print("TRIGGER GOOD")
            self.outputs.good_enough = True
            self.outputs.reason = ", ".join(good_metrics)
            self.outputs.set_disable = True
            return

        if self.get_input_value("timeout"):
            print("TRIGGER BAD")
            self.outputs.good_enough = False
            self.outputs.reason = "timeout"
            self.outputs.set_disable = True
            return

        if nmetrics == 4:
            print("TRIGGER BAD")
            self.outputs.good_enough = False
            self.outputs.reason = "none"
            self.outputs.set_disable = True
            return

        print("TRIGGER NOTHING")
        self.outputs.good_enough = None
        self.outputs.reason = None
        self.outputs.set_disable = False


class Good(Task, input_names=["reason"], output_names=["state", "reason"]):
    def run(self):
        print("\nGOOD:", self.inputs.reason)
        self.outputs.state = "GOOD"
        self.outputs.reason = self.inputs.reason


class Bad(Task, input_names=["reason"], output_names=["state", "reason"]):
    def run(self):
        print("\nBAD:", self.inputs.reason)
        self.outputs.state = "BAD"
        self.outputs.reason = self.inputs.reason


def workflow():
    nodes = [
        {"id": "required", "task_type": "class", "task_identifier": qualname(Required)},
        {"id": "metric1", "task_type": "class", "task_identifier": qualname(Metric)},
        {"id": "metric2", "task_type": "class", "task_identifier": qualname(Metric)},
        {"id": "metric3", "task_type": "class", "task_identifier": qualname(Metric)},
        {"id": "metric4", "task_type": "class", "task_identifier": qualname(Metric)},
        {"id": "timeout", "task_type": "class", "task_identifier": qualname(Timeout)},
        {"id": "decider", "task_type": "class", "task_identifier": qualname(Decider)},
        {"id": "good", "task_type": "class", "task_identifier": qualname(Good)},
        {"id": "bad", "task_type": "class", "task_identifier": qualname(Bad)},
    ]
    links = [
        {
            "source": "required",
            "target": "decider",
            "map_all_data": True,
        },
        {
            "source": "metric1",
            "target": "decider",
            "conditional": True,
            "cache_non_required": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric1"}],
        },
        {
            "source": "metric2",
            "target": "decider",
            "conditional": True,
            "cache_non_required": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric2"}],
        },
        {
            "source": "metric3",
            "target": "decider",
            "conditional": True,
            "cache_non_required": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric3"}],
        },
        {
            "source": "metric4",
            "target": "decider",
            "conditional": True,
            "cache_non_required": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric4"}],
        },
        {
            "source": "timeout",
            "target": "decider",
            "conditional": True,
            "cache_non_required": True,
            "data_mapping": [{"source_output": "timeout", "target_input": "timeout"}],
        },
        {
            "source": "decider",
            "target": "decider",
            "cache_non_required": True,
            "data_mapping": [
                {"source_output": "set_disable", "target_input": "disable"}
            ],
            "conditions": [{"source_output": "set_disable", "value": True}],
        },
        {
            "source": "decider",
            "target": "good",
            "data_mapping": [{"source_output": "reason", "target_input": "reason"}],
            "conditions": [{"source_output": "good_enough", "value": True}],
        },
        {
            "source": "decider",
            "target": "bad",
            "data_mapping": [{"source_output": "reason", "target_input": "reason"}],
            "conditions": [{"source_output": "good_enough", "value": False}],
        },
    ]
    return {"graph": {"id": "workflow"}, "nodes": nodes, "links": links}


def create_inputs(metric_threshold: float):
    tm = 0.1
    return [
        {"id": "required", "name": "compute_time", "value": 0.1 * tm},
        {"id": "metric1", "name": "compute_time", "value": 1 * tm},
        {"id": "metric1", "name": "metric", "value": 10},
        {"id": "metric2", "name": "compute_time", "value": 2 * tm},
        {"id": "metric2", "name": "metric", "value": 20},
        {"id": "metric3", "name": "compute_time", "value": 3 * tm},
        {"id": "metric3", "name": "metric", "value": 30},
        {"id": "timeout", "name": "timeout", "value": 4 * tm},
        {"id": "metric4", "name": "compute_time", "value": 5 * tm},
        {"id": "metric4", "name": "metric", "value": 40},
        {"id": "decider", "name": "metric_threshold", "value": metric_threshold},
    ]


def create_inputs_timeout_last(metric_threshold: float):
    tm = 0.1
    return [
        {"id": "required", "name": "compute_time", "value": 0.1 * tm},
        {"id": "metric1", "name": "compute_time", "value": 1 * tm},
        {"id": "metric1", "name": "metric", "value": 10},
        {"id": "metric2", "name": "compute_time", "value": 2 * tm},
        {"id": "metric2", "name": "metric", "value": 20},
        {"id": "metric3", "name": "compute_time", "value": 3 * tm},
        {"id": "metric3", "name": "metric", "value": 30},
        {"id": "metric4", "name": "compute_time", "value": 4 * tm},
        {"id": "metric4", "name": "metric", "value": 40},
        {"id": "timeout", "name": "timeout", "value": 5 * tm},
        {"id": "decider", "name": "metric_threshold", "value": metric_threshold},
    ]


def test_ppf_workflow25_metric1(ppf_log_config):
    """test 'cache_non_required' links"""
    # Metrics that pass: metric1, metric2, metric3 and metric4
    inputs = create_inputs(5)
    result = execute_graph(workflow(), inputs=inputs)
    assert result == {"reason": "metric1", "state": "GOOD"}


def test_ppf_workflow25_metric2(ppf_log_config):
    """test 'cache_non_required' links"""
    # Metrics that pass: metric2, metric3 and metric4
    inputs = create_inputs(15)
    result = execute_graph(workflow(), inputs=inputs)
    assert result == {"reason": "metric2", "state": "GOOD"}


def test_ppf_workflow25_metric3(ppf_log_config):
    """test 'cache_non_required' links"""
    # Metrics that pass: metric3 and metric4
    inputs = create_inputs(25)
    result = execute_graph(workflow(), inputs=inputs)
    assert result == {"reason": "metric3", "state": "GOOD"}


def test_ppf_workflow25_timeout1(ppf_log_config):
    """test 'cache_non_required' links"""
    # Metrics that pass: metric4
    inputs = create_inputs(35)
    result = execute_graph(workflow(), inputs=inputs)
    assert result == {"reason": "timeout", "state": "BAD"}


def test_ppf_workflow25_timeout2(ppf_log_config):
    """test 'cache_non_required' links"""
    # Metrics that pass: none
    inputs = create_inputs(45)
    result = execute_graph(workflow(), inputs=inputs)
    assert result == {"reason": "timeout", "state": "BAD"}


def test_ppf_workflow25_none(ppf_log_config):
    """test 'cache_non_required' links"""
    # Metrics that pass: none
    inputs = create_inputs_timeout_last(45)
    result = execute_graph(workflow(), inputs=inputs)
    assert result == {"reason": "none", "state": "BAD"}
