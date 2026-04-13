import json
import time
from pathlib import Path
from typing import Dict

import pytest
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
    optional_input_names=["metric1", "metric2", "metric3", "metric4", "timeout"],
    output_names=["good_enough", "reason"],
):
    def run(self):
        print("\nDecider executed with inputs:", self.get_input_values())

        # Check that we have all required inputs
        if self.inputs.param1 != -1:
            raise ValueError(f"param1 is {self.inputs.param1} intead of -1")

        if self.inputs.param2 != -2:
            raise ValueError(f"param2 is {self.inputs.param2} intead of -2")

        # Check the state of all metrics
        good_metrics = []
        bad_metrics = []
        unknown_metrics = []
        metric_names = ["metric1", "metric2", "metric3", "metric4"]
        for name in metric_names:
            value = self.get_input_value(name, None)
            if value is None:
                unknown_metrics.append(name)
            elif value >= self.inputs.metric_threshold:
                good_metrics.append(name)
            else:
                bad_metrics.append(name)

        print("Metrics that are good:", good_metrics)
        print("Metrics that are bad:", bad_metrics)
        print("Metrics that are unknown:", unknown_metrics)

        # Check timeout
        has_timeout = bool(self.get_input_value("timeout"))
        print("Timeout:", "yes" if has_timeout else "no")

        # Trigger downstream reasons
        trigger_good = len(good_metrics) == 1
        trigger_bad_timeout = has_timeout
        trigger_bad_none_good_enough = len(unknown_metrics) == 0

        # Ensure good/bad is trigger only once
        n = sum((bool(good_metrics), trigger_bad_timeout, trigger_bad_none_good_enough))
        if n > 1:
            trigger_good = False
            trigger_bad_timeout = False
            trigger_bad_none_good_enough = False

        # Trigger good, bas or nothing
        if trigger_good:
            print("TRIGGER GOOD")
            self.outputs.good_enough = True
            self.outputs.reason = ", ".join(good_metrics)
        elif trigger_bad_timeout:
            print("TRIGGER BAD: TIMEOUT")
            self.outputs.good_enough = False
            self.outputs.reason = "timeout"
        elif trigger_bad_none_good_enough:
            print("TRIGGER BAD: ALL METRIC BAD")
            self.outputs.good_enough = False
            self.outputs.reason = "no metric good enough"
        else:
            print("TRIGGER NOTHING")
            self.outputs.good_enough = None
            self.outputs.reason = None


class RecordCalls(Task, input_names=["call_record_file"]):
    def run(self):
        calls = json.loads(self.inputs.call_record_file.read_text())
        calls.append(self.get_output_values())
        self.inputs.call_record_file.write_text(json.dumps(calls))


class Good(RecordCalls, input_names=["reason"], output_names=["state", "reason"]):
    def run(self):
        print("\nGOOD:", self.inputs.reason)
        self.outputs.state = "GOOD"
        self.outputs.reason = self.inputs.reason
        super().run()


class Bad(RecordCalls, input_names=["reason"], output_names=["state", "reason"]):
    def run(self):
        print("\nBAD:", self.inputs.reason)
        self.outputs.state = "BAD"
        self.outputs.reason = self.inputs.reason
        super().run()


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
            "required": False,
            "cache_if_optional": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric1"}],
        },
        {
            "source": "metric2",
            "target": "decider",
            "required": False,
            "cache_if_optional": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric2"}],
        },
        {
            "source": "metric3",
            "target": "decider",
            "required": False,
            "cache_if_optional": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric3"}],
        },
        {
            "source": "metric4",
            "target": "decider",
            "required": False,
            "cache_if_optional": True,
            "data_mapping": [{"source_output": "metric", "target_input": "metric4"}],
        },
        {
            "source": "timeout",
            "target": "decider",
            "required": False,
            "cache_if_optional": True,
            "data_mapping": [{"source_output": "timeout", "target_input": "timeout"}],
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


def create_inputs(call_record_file: Path, metric_threshold: float):
    tm = 0.5  # Too short and the test fails. If that happens it is not a bug.
    # The Ewoks workflow SPECS have nothing to guarantee that downstream
    # execution follows the trigger order in time.
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
        {"id": "good", "name": "call_record_file", "value": call_record_file},
        {"id": "bad", "name": "call_record_file", "value": call_record_file},
    ]


def create_inputs_timeout_last(call_record_file: Path, metric_threshold: float):
    tm = 0.5  # Too short and the test fails. If that happens it is not a bug.
    # The Ewoks workflow SPECS have nothing to guarantee that downstream
    # execution follows the trigger order in time.
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
        {"id": "good", "name": "call_record_file", "value": call_record_file},
        {"id": "bad", "name": "call_record_file", "value": call_record_file},
    ]


@pytest.fixture
def call_record_file(tmp_path: Path):
    file = tmp_path / "calls.json"
    file.write_text(json.dumps([]))
    return file


def test_ppf_workflow25_metric1(ppf_log_config, call_record_file: Path):
    """test 'cache_if_optional' links"""
    # Metrics that pass: metric1, metric2, metric3 and metric4
    inputs = create_inputs(call_record_file, 5)
    result = execute_graph(workflow(), inputs=inputs)

    expected = {"state": "GOOD", "reason": "metric1"}
    calls = json.loads(call_record_file.read_text())
    assert calls == [expected]

    assert result == expected


def test_ppf_workflow25_metric2(ppf_log_config, call_record_file: Path):
    """test 'cache_if_optional' links"""
    # Metrics that pass: metric2, metric3 and metric4
    inputs = create_inputs(call_record_file, 15)
    result = execute_graph(workflow(), inputs=inputs)

    expected = {"state": "GOOD", "reason": "metric2"}
    _assert_result(call_record_file, result, expected)


def test_ppf_workflow25_metric3(ppf_log_config, call_record_file: Path):
    """test 'cache_if_optional' links"""
    # Metrics that pass: metric3 and metric4
    inputs = create_inputs(call_record_file, 25)
    result = execute_graph(workflow(), inputs=inputs)

    expected = {"state": "GOOD", "reason": "metric3"}
    _assert_result(call_record_file, result, expected)


def test_ppf_workflow25_timeout1(ppf_log_config, call_record_file: Path):
    """test 'cache_if_optional' links"""
    # Metrics that pass: metric4
    inputs = create_inputs(call_record_file, 35)
    result = execute_graph(workflow(), inputs=inputs)

    expected = {"state": "BAD", "reason": "timeout"}
    _assert_result(call_record_file, result, expected)


def test_ppf_workflow25_timeout2(ppf_log_config, call_record_file: Path):
    """test 'cache_if_optional' links"""
    # Metrics that pass: none
    inputs = create_inputs(call_record_file, 45)
    result = execute_graph(workflow(), inputs=inputs)

    expected = {"state": "BAD", "reason": "timeout"}
    _assert_result(call_record_file, result, expected)


def test_ppf_workflow25_timeout3(ppf_log_config, call_record_file: Path):
    """test 'cache_if_optional' links"""
    # Metrics that pass: none
    inputs = create_inputs_timeout_last(call_record_file, 45)
    result = execute_graph(workflow(), inputs=inputs)

    expected = {"state": "BAD", "reason": "no metric good enough"}
    _assert_result(call_record_file, result, expected)


def _assert_result(
    call_record_file: Path, result: Dict[str, str], expected: Dict[str, str]
) -> None:
    calls = json.loads(call_record_file.read_text())
    assert calls == [expected]
    assert result == expected
