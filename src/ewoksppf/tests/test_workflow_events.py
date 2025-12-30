from ewokscore.tests.test_workflow_events import assert_failed_workfow_events
from ewokscore.tests.test_workflow_events import assert_succesfull_workfow_events
from ewokscore.tests.test_workflow_events import fetch_events
from ewokscore.tests.test_workflow_events import run_failed_workfow
from ewokscore.tests.test_workflow_events import run_succesfull_workfow
from ewokscore.tests.test_workflow_events import sqlite_path  # noqa F401

from ewoksppf import execute_graph


def test_succesfull_workfow(sqlite_path):  # noqa F811
    # TODO: pypushflow does not work will asynchronous handlers because
    #       a worker could die before all queued events have been processed.
    database = sqlite_path / "ewoks_events.db"
    run_succesfull_workfow(database, execute_graph, execinfo={"asynchronous": False})
    events = fetch_events(database, 10)
    assert_succesfull_workfow_events(events)


def test_failed_workfow(sqlite_path):  # noqa F811
    database = sqlite_path / "ewoks_events.db"
    run_failed_workfow(database, execute_graph, execinfo={"asynchronous": False})
    events = fetch_events(database, 8)
    assert_failed_workfow_events(events)
