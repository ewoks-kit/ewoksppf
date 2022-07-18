from ewoksppf import execute_graph
from ewokscore.tests.test_workflow_events import fetch_events
from ewokscore.tests.test_workflow_events import run_succesfull_workfow
from ewokscore.tests.test_workflow_events import run_failed_workfow
from ewokscore.tests.test_workflow_events import assert_succesfull_workfow_events
from ewokscore.tests.test_workflow_events import assert_failed_workfow_events


def test_succesfull_workfow(tmpdir):
    # TODO: pypushflow does not work will asynchronous handlers because
    #       a worker could die before all queued events have been processed.
    uri = run_succesfull_workfow(
        tmpdir, execute_graph, execinfo={"asynchronous": False}
    )
    events = fetch_events(uri, 10)
    assert_succesfull_workfow_events(events)


def test_failed_workfow(tmpdir):
    uri = run_failed_workfow(tmpdir, execute_graph, execinfo={"asynchronous": False})
    events = fetch_events(uri, 8)
    assert_failed_workfow_events(events)
