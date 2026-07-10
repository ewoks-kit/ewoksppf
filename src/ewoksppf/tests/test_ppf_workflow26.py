import sys
import threading

from ewoksppf import execute_graph


def workflow26(limit: int):
    nodes = [
        {
            "id": "loop",
            "default_inputs": [
                {"name": "index", "value": 0},
                {"name": "limit", "value": limit},
            ],
            "force_start_node": True,
            "task_type": "ppfmethod",
            "task_identifier": "ewoksppf.tests.test_ppf_actors.pythonActorSelfLoop.run",
        },
    ]
    links = [
        {
            "source": "loop",
            "target": "loop",
            "conditions": [{"source_output": "has_data", "value": True}],
            "map_all_data": True,
        },
    ]
    graph = {"graph": {"id": "workflow26"}, "links": links, "nodes": nodes}
    expected_result = {"_ppfdict": {"index": limit, "limit": limit, "has_data": False}}
    return graph, expected_result


def test_workflow26(ppf_log_config):
    """Workflow that maximizes this race-condition in the workflow execution pool

    .. code-block:: python

        future = self._pool.submit(...)
        future.add_done_callback(cb)   # if worker already finished, `cb` runs in the current call stack

    See `test_input_merge_actor_reentrant_trigger` for deterministic counterpart.
    """
    graph, _ = workflow26(limit=200)

    # Lower GIL switch interval to make it more likely that
    # the submitted job finished before calling `future.add_done_callback`.
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        thread = threading.Thread(
            target=execute_graph,
            args=(graph,),
            kwargs={"pool_type": "thread"},
            daemon=True,
        )
        thread.start()
        thread.join(timeout=30)
    finally:
        sys.setswitchinterval(old_interval)

    assert not thread.is_alive(), "deadlocked InputMergeActor"
